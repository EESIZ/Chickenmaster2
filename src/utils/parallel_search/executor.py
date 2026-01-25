"""병렬 코루틴 실행을 위한 비동기 executor 모듈.

이 모듈은 세마포어를 사용한 동시성 제어와 부분 실패 처리를 지원하는
비동기 실행 유틸리티를 제공합니다.

Example:
    >>> import asyncio
    >>> from src.utils.parallel_search.executor import run_parallel
    >>> 
    >>> async def fetch_data(url: str) -> str:
    ...     # 데이터 페칭 로직
    ...     return f"data from {url}"
    >>> 
    >>> async def main():
    ...     factories = [
    ...         lambda u=url: fetch_data(u)
    ...         for url in ["http://a.com", "http://b.com"]
    ...     ]
    ...     results = await run_parallel(
    ...         factories,
    ...         max_concurrency=3,
    ...         timeout_s=10.0,
    ...     )
    ...     for r in results:
    ...         if r.success:
    ...             print(r.data)
    ...         else:
    ...             print(f"Error: {r.error}")
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Awaitable, Callable, TypeVar

from src.utils.parallel_search.base import TaskResult

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def _run_one(
    sem: asyncio.Semaphore,
    task_id: str,
    coro_factory: Callable[[], Awaitable[T]],
    timeout_s: float,
) -> TaskResult[T]:
    """단일 코루틴을 세마포어 및 타임아웃과 함께 실행합니다.

    세마포어를 획득한 후 코루틴을 실행하며, 타임아웃 내에
    완료되지 않으면 취소됩니다. 모든 예외는 캐치되어
    TaskResult로 래핑됩니다.

    Args:
        sem: 동시성 제어를 위한 세마포어.
        task_id: 작업 식별자 (로깅 및 결과 추적용).
        coro_factory: 코루틴을 생성하는 팩토리 함수.
            함수 호출 시 새로운 코루틴 인스턴스를 반환해야 합니다.
        timeout_s: 개별 작업 타임아웃 (초).

    Returns:
        작업 실행 결과를 담은 TaskResult 인스턴스.
        성공 시 data 필드에 결과가, 실패 시 error 필드에 에러 정보가 포함됩니다.

    Note:
        이 함수는 절대 예외를 발생시키지 않습니다.
        모든 예외는 TaskResult.fail()로 변환됩니다.
    """
    start_time = time.perf_counter()

    async with sem:
        try:
            logger.debug("작업 시작: %s", task_id)
            coro = coro_factory()
            result = await asyncio.wait_for(coro, timeout=timeout_s)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            logger.debug("작업 완료: %s (%.2fms)", task_id, elapsed_ms)
            return TaskResult.ok(
                task_id=task_id,
                data=result,
                elapsed_ms=elapsed_ms,
            )

        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning("작업 타임아웃: %s (%.2fms)", task_id, elapsed_ms)
            return TaskResult.fail(
                task_id=task_id,
                error=f"작업이 {timeout_s}초 내에 완료되지 않았습니다",
                error_type="TimeoutError",
                elapsed_ms=elapsed_ms,
            )

        except asyncio.CancelledError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning("작업 취소됨: %s (%.2fms)", task_id, elapsed_ms)
            return TaskResult.fail(
                task_id=task_id,
                error="작업이 취소되었습니다",
                error_type="CancelledError",
                elapsed_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "작업 실패: %s - %s: %s (%.2fms)",
                task_id,
                type(e).__name__,
                str(e),
                elapsed_ms,
            )
            return TaskResult.from_exception(
                task_id=task_id,
                exception=e,
                elapsed_ms=elapsed_ms,
            )


async def run_parallel(
    coro_factories: list[Callable[[], Awaitable[T]]],
    *,
    max_concurrency: int,
    timeout_s: float,
    task_ids: list[str] | None = None,
) -> list[TaskResult[T]]:
    """여러 코루틴을 세마포어로 제한된 동시성으로 병렬 실행합니다.

    모든 코루틴 팩토리를 병렬로 실행하되, 동시에 실행되는
    코루틴 수를 max_concurrency로 제한합니다. 개별 작업의
    실패가 전체 실행을 중단시키지 않습니다 (부분 실패 허용).

    Args:
        coro_factories: 코루틴을 생성하는 팩토리 함수 리스트.
            각 함수는 호출될 때마다 새로운 코루틴을 반환해야 합니다.
            람다나 functools.partial을 사용하여 인자를 바인딩하세요.
        max_concurrency: 최대 동시 실행 수.
            1 이상이어야 합니다. 너무 높으면 rate limit에 걸릴 수 있습니다.
        timeout_s: 개별 작업 타임아웃 (초).
            0보다 커야 합니다. 모든 작업이 이 시간 내에 완료되어야 합니다.
        task_ids: 각 작업의 식별자 리스트 (선택).
            제공되지 않으면 "task_0", "task_1", ... 형식으로 자동 생성됩니다.
            coro_factories와 같은 길이여야 합니다.

    Returns:
        TaskResult 인스턴스의 리스트.
        입력 순서와 동일한 순서로 결과가 반환됩니다.
        각 결과의 success 필드로 성공 여부를 확인할 수 있습니다.

    Raises:
        ValueError: max_concurrency < 1, timeout_s <= 0, 또는
            task_ids 길이가 coro_factories와 다른 경우.

    Example:
        >>> import asyncio
        >>> import httpx
        >>> 
        >>> async def fetch_url(url: str) -> str:
        ...     async with httpx.AsyncClient() as client:
        ...         response = await client.get(url)
        ...         return response.text
        >>> 
        >>> async def main():
        ...     urls = ["https://example.com", "https://google.com"]
        ...     factories = [lambda u=url: fetch_url(u) for url in urls]
        ...     results = await run_parallel(
        ...         factories,
        ...         max_concurrency=2,
        ...         timeout_s=30.0,
        ...         task_ids=[f"fetch_{i}" for i in range(len(urls))],
        ...     )
        ...     
        ...     successful = [r for r in results if r.success]
        ...     failed = [r for r in results if not r.success]
        ...     print(f"성공: {len(successful)}, 실패: {len(failed)}")

    Note:
        - 코루틴 팩토리를 사용하는 이유: 코루틴은 한 번만 await할 수 있으므로,
          재시도나 취소 후 재실행이 필요할 때 새로운 코루틴을 생성해야 합니다.
        - 세마포어는 rate limiting이 아닌 동시성 제한용입니다.
          API rate limit 준수는 각 provider가 담당합니다.
    """
    # 입력 검증
    if max_concurrency < 1:
        raise ValueError(f"max_concurrency는 1 이상이어야 합니다: {max_concurrency}")
    if timeout_s <= 0:
        raise ValueError(f"timeout_s는 0보다 커야 합니다: {timeout_s}")

    n_tasks = len(coro_factories)

    # task_ids 검증 및 기본값 생성
    if task_ids is None:
        task_ids = [f"task_{i}" for i in range(n_tasks)]
    elif len(task_ids) != n_tasks:
        raise ValueError(
            f"task_ids 길이({len(task_ids)})가 "
            f"coro_factories 길이({n_tasks})와 다릅니다"
        )

    if n_tasks == 0:
        logger.debug("실행할 작업이 없습니다")
        return []

    logger.info(
        "병렬 실행 시작: %d개 작업, max_concurrency=%d, timeout=%ss",
        n_tasks,
        max_concurrency,
        timeout_s,
    )

    # 세마포어 생성 및 작업 실행
    sem = asyncio.Semaphore(max_concurrency)
    tasks = [
        asyncio.create_task(_run_one(sem, task_id, factory, timeout_s))
        for task_id, factory in zip(task_ids, coro_factories)
    ]

    # 모든 작업 완료 대기 (gather는 결과 순서를 유지함)
    results = await asyncio.gather(*tasks, return_exceptions=False)

    # 결과 통계 로깅
    successful = sum(1 for r in results if r.success)
    failed = n_tasks - successful
    total_time_ms = sum(r.elapsed_ms for r in results)

    logger.info(
        "병렬 실행 완료: 성공=%d, 실패=%d, 총 소요시간=%.2fms",
        successful,
        failed,
        total_time_ms,
    )

    return results


async def run_parallel_with_retry(
    coro_factories: list[Callable[[], Awaitable[T]]],
    *,
    max_concurrency: int,
    timeout_s: float,
    max_retries: int = 3,
    retry_delay_s: float = 1.0,
    task_ids: list[str] | None = None,
    retry_on: tuple[type[Exception], ...] | None = None,
) -> list[TaskResult[T]]:
    """실패한 작업에 대해 재시도를 수행하는 병렬 실행기.

    run_parallel과 동일하지만 실패한 작업에 대해
    지수 백오프로 재시도를 수행합니다.

    Args:
        coro_factories: 코루틴 팩토리 함수 리스트.
        max_concurrency: 최대 동시 실행 수.
        timeout_s: 개별 작업 타임아웃 (초).
        max_retries: 최대 재시도 횟수 (기본값: 3).
        retry_delay_s: 초기 재시도 지연 시간 (초, 기본값: 1.0).
            재시도할 때마다 지수적으로 증가합니다.
        task_ids: 각 작업의 식별자 리스트 (선택).
        retry_on: 재시도할 예외 타입 튜플 (선택).
            None이면 TimeoutError와 ConnectionError만 재시도합니다.

    Returns:
        TaskResult 인스턴스의 리스트 (입력 순서 유지).

    Example:
        >>> results = await run_parallel_with_retry(
        ...     factories,
        ...     max_concurrency=3,
        ...     timeout_s=10.0,
        ...     max_retries=3,
        ...     retry_delay_s=1.0,
        ... )
    """
    if retry_on is None:
        retry_on = (TimeoutError, ConnectionError, asyncio.TimeoutError)

    n_tasks = len(coro_factories)
    if task_ids is None:
        task_ids = [f"task_{i}" for i in range(n_tasks)]

    # 초기 실행
    results = await run_parallel(
        coro_factories,
        max_concurrency=max_concurrency,
        timeout_s=timeout_s,
        task_ids=task_ids,
    )

    # 재시도 루프
    for attempt in range(max_retries):
        # 재시도 대상 찾기
        retry_indices: list[int] = []
        for i, result in enumerate(results):
            if not result.success and result.error_type in [
                exc.__name__ for exc in retry_on
            ]:
                retry_indices.append(i)

        if not retry_indices:
            logger.debug("재시도할 작업 없음")
            break

        # 지수 백오프 대기
        delay = retry_delay_s * (2**attempt)
        logger.info(
            "재시도 %d/%d: %d개 작업, %.2f초 후 시작",
            attempt + 1,
            max_retries,
            len(retry_indices),
            delay,
        )
        await asyncio.sleep(delay)

        # 재시도 실행
        retry_factories = [coro_factories[i] for i in retry_indices]
        retry_task_ids = [f"{task_ids[i]}_retry{attempt + 1}" for i in retry_indices]

        retry_results = await run_parallel(
            retry_factories,
            max_concurrency=max_concurrency,
            timeout_s=timeout_s,
            task_ids=retry_task_ids,
        )

        # 결과 업데이트
        for idx, retry_result in zip(retry_indices, retry_results):
            if retry_result.success:
                results[idx] = retry_result

    return results


__all__ = [
    "run_parallel",
    "run_parallel_with_retry",
]
