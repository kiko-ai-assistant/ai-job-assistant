from pydantic import BaseModel, Field


class ChannelConfig(BaseModel):
    username: str
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)


class ChannelsConfigFile(BaseModel):
    channels: list[ChannelConfig] = Field(default_factory=list)
