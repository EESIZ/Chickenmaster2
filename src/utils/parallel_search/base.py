"""병렬 검색을 위한 기본 추상화 모듈.

이 모듈은 다양한 검색 제공자를 통합하기 위한 핵심 인터페이스와
데이터 구조를 정의합니다.

Example:
    >>> from src.utils.parallel_search.base import SearchResult, SearchProvider
    >>> 
    >>> class MyProvider(SearchProvider):
    ...     async def search(self, query: str) -> list[SearchResult]:
    ...         # 구현
    ...         pass
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class SearchResult:
    """검색 결과를 나타내는 불변 데이터 클래스.

    각 검색 제공자로부터 반환된 개별 결과를 표준화된 형식으로 저장합니다.

    Attributes:
        provider: 결과를 제공한 검색 제공자의 식별자 (예: "google", "arxiv").
        query: 이 결과를 생성한 원본 검색 쿼리.
        title: 검색 결과의 제목.
        url: 결과 페이지의 URL.
        ids: 제공자별 고유 식별자 딕셔너리 (예: {"arxiv_id": "2401.12345", "doi": "10.1234/..."}).
        snippet: 결과의 요약 또는 미리보기 텍스트.
        score: 관련성 점수 (0.0 ~ 1.0, 높을수록 관련성이 높음).
        fetched_at: 결과를 가져온 시각 (UTC).

    Example:
        >>> result = SearchResult(
        ...     provider="arxiv",
        ...     query="transformer attention",
        ...     title="Attention Is All You Need",
        ...     url="https://arxiv.org/abs/1706.03762",
        ...     ids={"arxiv_id": "1706.03762"},
        ...     snippet="The dominant sequence transduction models...",
        ...     score=0.95,
        ...     fetched_at=datetime.utcnow(),
        ... )
    """

    provider: str
    query: str
    title: str
    url: str
    ids: dict[str, str] = field(default_factory=dict)
    snippet: str = ""
    score: float = 0.0
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """데이터 유효성 검증."""
        if not 0.0 <= self.score <= 1.0:
            # frozen=True이므로 object.__setattr__ 사용
            object.__setattr__(self, "score", max(0.0, min(1.0, self.score)))


@dataclass(frozen=True, slots=True)
class TaskResult(Generic[T]):
    """비동기 작업 결과를 래핑하는 제네릭 데이터 클래스.

    성공한 결과와 실패한 결과를 모두 표현할 수 있으며,
    에러 정보와 실행 시간을 함께 저장합니다.

    Attributes:
        task_id: 작업 식별자.
        success: 작업 성공 여부.
        data: 성공 시 결과 데이터 (실패 시 None).
        error: 실패 시 에러 메시지 (성공 시 None).
        error_type: 실패 시 예외 타입 이름 (성공 시 None).
        elapsed_ms: 작업 실행 시간 (밀리초).
        started_at: 작업 시작 시각 (UTC).

    Example:
        >>> # 성공한 결과
        >>> success_result = TaskResult(
        ...     task_id="search_google_001",
        ...     success=True,
        ...     data=[SearchResult(...)],
        ...     elapsed_ms=150.5,
        ... )
        >>> 
        >>> # 실패한 결과
        >>> error_result = TaskResult[list[SearchResult]](
        ...     task_id="search_arxiv_002",
        ...     success=False,
        ...     error="Connection timeout",
        ...     error_type="TimeoutError",
        ...     elapsed_ms=30000.0,
        ... )
    """

    task_id: str
    success: bool
    data: T | None = None
    error: str | None = None
    error_type: str | None = None
    elapsed_ms: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def ok(cls, task_id: str, data: T, elapsed_ms: float = 0.0) -> TaskResult[T]:
        """성공한 결과를 생성하는 팩토리 메서드.

        Args:
            task_id: 작업 식별자.
            data: 결과 데이터.
            elapsed_ms: 실행 시간 (밀리초).

        Returns:
            성공 상태의 TaskResult 인스턴스.
        """
        return cls(
            task_id=task_id,
            success=True,
            data=data,
            elapsed_ms=elapsed_ms,
        )

    @classmethod
    def fail(
        cls,
        task_id: str,
        error: str,
        error_type: str | None = None,
        elapsed_ms: float = 0.0,
    ) -> TaskResult[T]:
        """실패한 결과를 생성하는 팩토리 메서드.

        Args:
            task_id: 작업 식별자.
            error: 에러 메시지.
            error_type: 예외 타입 이름.
            elapsed_ms: 실행 시간 (밀리초).

        Returns:
            실패 상태의 TaskResult 인스턴스.
        """
        return cls(
            task_id=task_id,
            success=False,
            error=error,
            error_type=error_type,
            elapsed_ms=elapsed_ms,
        )

    @classmethod
    def from_exception(
        cls,
        task_id: str,
        exception: BaseException,
        elapsed_ms: float = 0.0,
    ) -> TaskResult[T]:
        """예외로부터 실패 결과를 생성하는 팩토리 메서드.

        Args:
            task_id: 작업 식별자.
            exception: 발생한 예외.
            elapsed_ms: 실행 시간 (밀리초).

        Returns:
            실패 상태의 TaskResult 인스턴스.
        """
        return cls.fail(
            task_id=task_id,
            error=str(exception),
            error_type=type(exception).__name__,
            elapsed_ms=elapsed_ms,
        )


class SearchProvider(ABC):
    """검색 제공자를 위한 추상 기본 클래스.

    모든 검색 제공자(Google, Arxiv, Semantic Scholar 등)는
    이 클래스를 상속받아 구현해야 합니다.

    Subclasses must implement:
        - search(): 실제 검색을 수행하는 비동기 메서드

    Attributes:
        name: 제공자 이름 (서브클래스에서 오버라이드 가능).
        _max_concurrency: 최대 동시 요청 수.
        _timeout_s: 요청 타임아웃 (초).

    Example:
        >>> class GoogleSearchProvider(SearchProvider):
        ...     def __init__(self, api_key: str):
        ...         super().__init__(max_concurrency=5, timeout_s=10.0)
        ...         self._api_key = api_key
        ...
        ...     @property
        ...     def name(self) -> str:
        ...         return "google"
        ...
        ...     async def search(self, query: str) -> list[SearchResult]:
        ...         # Google API 호출 구현
        ...         pass
    """

    def __init__(
        self,
        max_concurrency: int = 3,
        timeout_s: float = 30.0,
    ) -> None:
        """SearchProvider를 초기화합니다.

        Args:
            max_concurrency: 최대 동시 요청 수 (기본값: 3).
            timeout_s: 요청 타임아웃 초 (기본값: 30.0).

        Raises:
            ValueError: max_concurrency가 1 미만이거나 timeout_s가 0 이하인 경우.
        """
        if max_concurrency < 1:
            raise ValueError(f"max_concurrency는 1 이상이어야 합니다: {max_concurrency}")
        if timeout_s <= 0:
            raise ValueError(f"timeout_s는 0보다 커야 합니다: {timeout_s}")

        self._max_concurrency = max_concurrency
        self._timeout_s = timeout_s

    @property
    def name(self) -> str:
        """제공자 이름을 반환합니다.

        기본적으로 클래스 이름에서 'Provider' 접미사를 제거하고
        소문자로 변환합니다. 서브클래스에서 오버라이드할 수 있습니다.

        Returns:
            제공자 식별자 문자열.
        """
        class_name = self.__class__.__name__
        if class_name.endswith("Provider"):
            class_name = class_name[:-8]  # "Provider" 제거
        return class_name.lower()

    @property
    def max_concurrency(self) -> int:
        """최대 동시 요청 수를 반환합니다.

        Returns:
            동시에 실행할 수 있는 최대 요청 수.
        """
        return self._max_concurrency

    @property
    def timeout_s(self) -> float:
        """요청 타임아웃을 초 단위로 반환합니다.

        Returns:
            타임아웃 시간 (초).
        """
        return self._timeout_s

    @abstractmethod
    async def search(self, query: str) -> list[SearchResult]:
        """주어진 쿼리로 검색을 수행합니다.

        이 메서드는 서브클래스에서 반드시 구현해야 합니다.
        구현 시 다음 사항을 준수해야 합니다:
        - 네트워크 에러 시 적절한 예외 발생
        - 타임아웃 준수 (self.timeout_s 사용)
        - 결과를 SearchResult 형식으로 변환

        Args:
            query: 검색 쿼리 문자열.

        Returns:
            검색 결과 리스트. 결과가 없으면 빈 리스트 반환.

        Raises:
            NotImplementedError: 서브클래스에서 구현되지 않은 경우.
            TimeoutError: 요청이 타임아웃된 경우.
            ConnectionError: 네트워크 연결 실패 시.
        """
        raise NotImplementedError("서브클래스에서 search() 메서드를 구현해야 합니다")

    def __repr__(self) -> str:
        """객체의 문자열 표현을 반환합니다."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"max_concurrency={self.max_concurrency}, "
            f"timeout_s={self.timeout_s})"
        )


__all__ = [
    "SearchResult",
    "SearchProvider",
    "TaskResult",
]
