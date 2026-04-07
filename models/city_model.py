from beanie import Document


class City(Document):
    id: str
    name: str
    state: str
    country: str
    location: str | None = None
    timezone: str | None = None
    show_in_onboarding: bool
    state_full_name: str
    show_in_app: bool

    class Settings:
        name = "cities"
