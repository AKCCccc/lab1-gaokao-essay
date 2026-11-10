from typing import Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200, description="作文题目")
    material: str = Field("", max_length=4000, description="题目材料或写作要求")
    genre: Literal["议论文", "记叙文", "散文", "书信"] = "议论文"
    word_count: int = Field(800, ge=600, le=1200, description="目标字数")
    style: Literal["满分冲刺", "稳健高分", "思辨深刻", "文采斐然"] = "满分冲刺"
    extra: str = Field("", max_length=1000, description="附加要求")
    mode: Literal["standard", "fast"] = Field("standard", description="standard=先大纲后成文")
    outline: str = Field("", max_length=6000, description="已生成的大纲")


class ReviewRequest(BaseModel):
    title: str = Field("", max_length=200)
    essay: str = Field(..., min_length=100, max_length=12000)
