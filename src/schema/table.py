from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DomainTaxonomy(BaseModel):
    parent_domain: str = Field(..., description="Top-tier logical entity root e.g., 'expense_domain'")
    sub_domain: str = Field(..., description="Middle-tier architectural bound e.g., 'billing_configurations'")
    hierarchy_path: str = Field(..., description="Full path string using format: parent > child > table")
    depth_level: int = Field(default=3, description="Depth level indicator in taxonomy tree structures")

class PerformanceGuard(BaseModel):
    indexed_columns: List[str]
    unindexed_columns: List[str]
    max_unlimited_row_safety_limit: int
    llm_instruction: str

class TimeStandard(BaseModel):
    database_timezone: str
    temporal_columns: Dict[str, str]
    llm_instruction: str

class SynonymMap(BaseModel):
    synonyms: Dict[str, str]
    llm_instruction: str

class CrossDomainLink(BaseModel):
    local_column: str
    target_path: str = Field(..., description="Target domain hierarchy path e.g., 'user_domain > assets > assets'")
    relationship_type: str = Field(..., description="Structural mapping relationship e.g., 'HAS_A', 'BELONGS_TO'")
    description: str

class TableContext(BaseModel):
    table_name: str
    taxonomy: DomainTaxonomy  # Swapped direct physical DB routing configuration layout with the Abstract Taxonomy Map
    description: str
    detailed_description: Optional[str] = None
    query_complexity_weight: str = "LOW"
    orchestration_action_required: str = "NONE"

    # Core structural elements
    ddl_statement: str
    columns: List[Dict[str, Any]]
    foreign_keys: List[Dict[str, Any]]
    common_join_patterns: List[str] = Field(default_factory=list)
    cross_domain_links: List[CrossDomainLink] = Field(default_factory=list) # Updated parameter name & type blueprint

    # Advanced LLM Alignment parameters
    performance_and_indexing_guardrails: Optional[PerformanceGuard] = None
    time_and_timezone_standards: Optional[TimeStandard] = None
    aggregation_and_math_rules: Optional[Dict[str, Any]] = None
    value_mappings_and_synonyms: Optional[Dict[str, SynonymMap]] = None

    filtering_rules_and_guardrails: Optional[Dict[str, str]] = None
    llm_sql_hints_and_gotchas: List[str] = Field(default_factory=list)
    unsupported_queries_and_limitations: Optional[Dict[str, str]] = None
    sample_values: Dict[str, List[Any]] = Field(default_factory=dict)