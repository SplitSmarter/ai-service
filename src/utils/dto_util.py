# src/utils/dto_utils.py
import json
import logging
import re
from typing import Type, TypeVar
from fastapi import HTTPException, status
from pydantic import BaseModel

from src.dto.agent import GenerationResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class DTOUtils:
    """Utility class for parsing and converting LLM generation outputs into structured Pydantic DTOs."""

    @staticmethod
    def parse_llm_response(
        gen_response: GenerationResponse,
        target_model: Type[T]
    ) -> T:
        """
        Strips markdown code fences (```json ... ```) from the LLM text output,
        parses the JSON payload, and validates it into the requested Pydantic model.
        """
        try:
            raw_text = gen_response.text or ""
            # Strip out leading ```json/``` and trailing ``` markdown wrappers
            cleaned_str = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)

            parsed_dict = json.loads(cleaned_str)
            return target_model.model_validate(parsed_dict)

        except json.JSONDecodeError as jde:
            logger.error(f"Failed to decode JSON from LLM response: {str(jde)}\nRaw text: {gen_response.text}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"LLM output is not valid JSON: {str(jde)}"
            )
        except Exception as e:
            logger.error(f"Failed to parse LLM text into {target_model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to validate LLM output into {target_model.__name__}: {str(e)}"
            )