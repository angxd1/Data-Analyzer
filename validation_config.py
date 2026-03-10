from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationRules:
    id_uniqueness_threshold: float = 0.98
    constant_dominant_ratio: float = 0.95
    datetime_regex_threshold: float = 0.6
    datetime_parse_threshold: float = 0.8
    epoch_seconds_min: int = 1_000_000_000
    epoch_seconds_max: int = 2_000_000_000
    epoch_millis_min: int = 1_000_000_000_000
    epoch_millis_max: int = 2_000_000_000_000
    high_cardinality_unique_min: int = 5
    high_cardinality_ratio_threshold: float = 0.8
    high_cardinality_count_threshold: int = 50
    numeric_as_categorical_unique_max: int = 15
    numeric_as_categorical_range_max: float = 50.0
    near_zero_std_threshold: float = 1e-6
    skew_threshold: float = 2.0
    outlier_ratio_threshold: float = 0.1
    dominant_numeric_mode_threshold: float = 0.5
    id_name_tokens: set[str] = field(
        default_factory=lambda: {
            "id",
            "uuid",
            "guid",
            "key",
            "index",
            "identifier",
            "record",
            "account",
            "customer",
            "user",
            "order",
            "transaction",
            "session",
        }
    )
    datetime_name_tokens: set[str] = field(
        default_factory=lambda: {
            "date",
            "time",
            "timestamp",
            "datetime",
            "created",
            "updated",
            "signup",
            "login",
            "event",
            "start",
            "end",
        }
    )


DEFAULT_VALIDATION_RULES = ValidationRules()
