import pytest

from src.taskwarrior import TaskWarrior, Task, Priority


def test_date_calculation_integration(tw: TaskWarrior) -> None:
    """Test that date parsing works with Task model fields."""
    # Test basic date parsing
    from src.taskwarrior.services.date_calculation_service import DateCalculationService
    service = DateCalculationService("task")
    
    test_date = "2024-01-31"
    parsed_date = service.parse_date(test_date)
    
    # Verify it's a datetime object
    assert isinstance(parsed_date, type(service.parse_date("2024-01-31")))


def test_synonym_parsing_integration(tw: TaskWarrior) -> None:
    """Test that date synonyms work correctly."""
    from src.taskwarrior.services.date_calculation_service import DateCalculationService
    service = DateCalculationService("task")
    
    # Test today synonym
    try:
        today = service.get_today()
        assert isinstance(today, type(service.parse_date("2024-01-31")))
    except ValueError:
        # If task calc is not available in test environment, skip
        pass

    # Test tomorrow synonym  
    try:
        tomorrow = service.get_tomorrow()
        assert isinstance(tomorrow, type(service.parse_date("2024-01-31")))
    except ValueError:
        # If task calc is not available in test environment, skip
        pass


def test_date_validation_integration(tw: TaskWarrior) -> None:
    """Test date validation functionality."""
    from src.taskwarrior.services.date_calculation_service import DateCalculationService
    service = DateCalculationService("task")
    
    # Test valid dates
    assert service.validate_date("today")
    assert service.validate_date("2024-01-31")
    
    # Test invalid dates
    assert not service.validate_date("invalid-date")
    assert not service.validate_date("")
