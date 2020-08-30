from typing import Callable, Generic, Sequence, TypeVar, Union
from graia.application.message.elements import InternalElement, ExternalElement
from graia.broadcast.entities.decorater import Decorater
from graia.broadcast.interfaces.decorater import DecoraterInterface
from graia.application.entry import MessageChain

T = TypeVar("T")

class Components(Decorater, Generic[T]):
    _filter: Callable[[Union[InternalElement, ExternalElement]], bool]
    _match_times: int = float("inf")
    _skip_times: int = 0

    def __init__(self,
            filter_callable: Callable[[Union[InternalElement, ExternalElement]], bool],
            match_times: int = float("inf"),
            skip_times: int = 0) -> None:
        self._filter = filter_callable
        self._match_times = match_times
        self._skip_times = skip_times

    @classmethod
    def __class_getitem__(cls,
        item: Union[
            Union[InternalElement, ExternalElement],
            Sequence[Union[InternalElement, ExternalElement]],
            slice
        ]
    ) -> "Components":
        _element_type, match_times = None, float("inf")
        if isinstance(item, slice):
            if item.stop <= 0:
                raise TypeError("you should put a positive number.")
            element_type, match_times = item.start, item.stop
        else: # 因为是用的 isinstance 判断, 所以问题不大(isinstance 第二个参数允许是 tuple.)
            if isinstance(item, list):
                item = tuple(item)
            element_type = item

        def matcher(element: Union[InternalElement, ExternalElement]):
            return isinstance(element, element_type)

        return cls(matcher, match_times)

    async def target(self, interface: DecoraterInterface):
        chain: MessageChain
        if interface.annotation != MessageChain:
            chain = await interface.dispatcher_interface.execute_with("message", MessageChain)
        else:
            chain = interface.return_value
        
        selected = []
        matched_times = 0
        for value in chain.__root__:
            if matched_times >= self._match_times + self._skip_times:
                break
            if self._filter(value):
                selected.append(value)
                matched_times += 1

        return MessageChain.create(selected[self._skip_times:])
