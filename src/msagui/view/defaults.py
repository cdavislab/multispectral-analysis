from dataclasses import dataclass

@dataclass
class ViewDefaults:
    font_family: str = 'Verdana'
    font_size: int = 10
    justify: str = "center"
    bg: str = "#e9e9ed"
    fg: str = "#000000"
    blue: str = "#08a1f7"