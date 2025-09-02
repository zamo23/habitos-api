from datetime import datetime

def parse_date(date_str: str) -> datetime:
    """
    Parsea una fecha string en formato YYYY-MM-DD a objeto datetime
    
    Args:
        date_str: String de fecha en formato YYYY-MM-DD
        
    Returns:
        datetime: Objeto datetime correspondiente a la fecha
        
    Raises:
        ValueError: Si el formato de fecha es inválido
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError as e:
        raise ValueError(f"Formato de fecha inválido. Use YYYY-MM-DD: {str(e)}")
