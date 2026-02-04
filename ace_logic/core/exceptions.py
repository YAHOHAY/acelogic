# ace_logic/core/exceptions.py

class AceLogicError(Exception):
    """AceLogic 项目的所有异常基类 (Base class for all exceptions)"""
    pass

class DeckError(AceLogicError):
    """牌堆相关异常 (Exception raised for errors in the deck)"""
    pass

class InsufficientCardsError(DeckError):
    """当牌堆剩余牌数不足时抛出 (Raised when deck has fewer cards than requested)"""
    pass

class EvaluatorError(AceLogicError):
    """判定器相关异常 (Exception raised for errors in hand evaluation)"""
    pass

class InvalidHandSizeError(EvaluatorError):
    """当传入判定器的手牌数量不是 5 张时抛出 (Raised when hand size is not exactly 5)"""
    pass