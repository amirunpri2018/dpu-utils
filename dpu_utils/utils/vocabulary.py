from collections import Counter
from typing import Iterable, Dict, Sized, List, FrozenSet, Union

import numpy as np


class Vocabulary(Sized):
    """
    A simple vocabulary that maps strings to unique ids (and back).
    """

    def __init__(self, add_unk: bool=True) -> None:
        self.token_to_id = {}  # type: Dict[str, int]
        self.id_to_token = []  # type: List[str]
        if add_unk:
            self.add_or_get_id(self.get_unk())

    def is_equal_to(self, other) -> bool:
        """
        This would be __eq__, except that Python 3 insists that __hash__ is defined if __eq__ is
        defined, and we can't define __hash__ because the object is mutable.
        """
        if type(other) != Vocabulary:
            return False
        return self.id_to_token == other.id_to_token

    def add_or_get_id(self, token: str) -> int:
        """
        Get the token's id. If the token does not exist in the
        dictionary, add it.
        """
        this_id = self.token_to_id.get(token)
        if this_id is not None:
            return this_id

        this_id = len(self.id_to_token)
        self.token_to_id[token] = this_id
        self.id_to_token.append(token)
        return this_id

    def is_unk(self, token: str) -> bool:
        return token not in self.token_to_id

    def get_id_or_unk(self, token: str) -> int:
        this_id = self.token_to_id.get(token)
        if this_id is not None:
            return this_id
        else:
            return self.token_to_id[self.get_unk()]

    def get_name_for_id(self, token_id: int) -> str:
        return self.id_to_token[token_id]

    def __len__(self) -> int:
        return len(self.token_to_id)

    def __str__(self):
        return str(self.token_to_id)

    def get_all_names(self) -> FrozenSet[str]:
        return frozenset(self.token_to_id.keys())

    def __batch_add_from_counter(self, token_counter: Counter, count_threshold: int, max_size:int) -> None:
        """Update dictionary with elements of the token_counter"""
        for token, count in token_counter.most_common(max_size):
            if count >= count_threshold:
                self.add_or_get_id(token)
            else:
                break

    @staticmethod
    def get_unk() -> str:
        return '%UNK%'

    @staticmethod
    def create_vocabulary(tokens: Union[Iterable[str], Counter], max_size: int,
                          count_threshold: int=5, add_unk: bool=True) -> 'Vocabulary':
        if type(tokens) is Counter:
            token_counter = tokens
        else:
            token_counter = Counter(tokens)
        vocab = Vocabulary(add_unk=add_unk)
        vocab.__batch_add_from_counter(token_counter, count_threshold, max_size - (1 if add_unk else 0))
        return vocab

    def update(self, token_counter: Counter, max_size: int, count_threshold: int=5):
        assert len(self) < max_size, 'Dictionary is already larger than max_size.'
        self.__batch_add_from_counter(token_counter, count_threshold=count_threshold, max_size=max_size)

    def get_empirical_distribution(self, elements: Iterable[str], dirichlet_alpha: float=10.) -> np.ndarray:
        """Retrieve empirical distribution of elements."""
        targets = np.fromiter((self.get_id_or_unk(t) for t in elements), dtype=np.int)
        empirical_distribution = np.bincount(targets, minlength=len(self)).astype(float)
        empirical_distribution += dirichlet_alpha / len(empirical_distribution)
        return empirical_distribution / (np.sum(empirical_distribution) + dirichlet_alpha)
