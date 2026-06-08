# models/ticket_schemas.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class SupportTicket(BaseModel):
	#Модель валидации тикета поддержки

	ticket_id: str = Field(
		..., 
		pattern=r'^TCKT-2026-\d{6}$',
		description="ID тикета в формате TCKT-2026-XXXXXX"
	)
	user_id: str = Field(
		..., 
		pattern=r'^u_\d{4}$',
		description="ID пользователя в формате u_XXXX"
	)
	priority: str = Field(..., description="Приоритет: low, medium, high, urgent")
	category: str = Field(..., description="Категория: payment, delivery, technical, account")
	resolution_minutes: int = Field(
		..., 
		gt=0, 
		le=10080,
		description="Время решения в минутах (от 1 до 10080)"
	)
	channel: str = Field(..., description="Канал: chat, email, phone")
	created_at: datetime = Field(..., description="Дата создания тикета")
	loaded_at: datetime | None = Field(None, description="Дата загрузки в PostgreSQL")

	@field_validator('priority')
	@classmethod
	def validate_priority(cls, v: str) -> str:
		allowed = ["low", "medium", "high", "urgent"]
		if v not in allowed:
			raise ValueError(
				f'Приоритет "{v}" недопустим. Допустимые значения: low, medium, high, urgent'
			)
		return v

	@field_validator('category')
	@classmethod
	def validate_category(cls, v: str) -> str:
		allowed = ["payment", "delivery", "technical", "account"]
		if v not in allowed:
			raise ValueError(
				f'Категория "{v}" недопустима. Допустимые значения: payment, delivery, technical, account'
			)
		return v

	@field_validator('channel')
	@classmethod
	def validate_channel(cls, v: str) -> str:
		allowed = ["chat", "email", "phone"]
		if v not in allowed:
			raise ValueError(
				f'Канал "{v}" недопустим. Допустимые значения: chat, email, phone'
			)
		return v