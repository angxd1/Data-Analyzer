from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ValidationFinding:
    column: str
    warning: str
    uniqueness_ratio: float | None = None
    monotonic: str | None = None
    integer_like: bool | None = None
    dominant_value_pct: float | None = None
    unique_values: int | None = None
    method: str | None = None
    parsed_ratio: float | None = None
    inferred_format: str | None = None
    unique_count: int | None = None
    ratio: float | None = None
    range: float | None = None
    metric: str | None = None
    severity: int | None = None

    def to_dict(self) -> dict:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class SchemaSummary:
    total_rows: int
    total_columns: int
    numeric_count: int
    categorical_count: int
    datetime_count: int
    missing_pct: float
    duplicate_rows_pct: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ValidationResult:
    id_columns: list[ValidationFinding] = field(default_factory=list)
    constant_columns: list[ValidationFinding] = field(default_factory=list)
    datetime_columns: list[ValidationFinding] = field(default_factory=list)
    high_cardinality: list[ValidationFinding] = field(default_factory=list)
    numeric_as_categorical: list[ValidationFinding] = field(default_factory=list)
    distribution_warnings: list[ValidationFinding] = field(default_factory=list)
    schema_summary: SchemaSummary = field(
        default_factory=lambda: SchemaSummary(0, 0, 0, 0, 0, 0.0, 0.0)
    )

    def to_dict(self) -> dict:
        return {
            "id_columns": [item.to_dict() for item in self.id_columns],
            "constant_columns": [item.to_dict() for item in self.constant_columns],
            "datetime_columns": [item.to_dict() for item in self.datetime_columns],
            "high_cardinality": [item.to_dict() for item in self.high_cardinality],
            "numeric_as_categorical": [
                item.to_dict() for item in self.numeric_as_categorical
            ],
            "distribution_warnings": [
                item.to_dict() for item in self.distribution_warnings
            ],
            "schema_summary": self.schema_summary.to_dict(),
        }
