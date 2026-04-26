# Test Result History

**Builds tracked:** 4  |  **Test cases tracked:** 69

## Build Summary

| Build ID | Run | SHA | Passed | Failed | Total |
|----------|-----|-----|--------|--------|-------|
| `001-a1b2c3d` | #1 | `a1b2c3d` | 67 | 2 | 69 |
| `002-e4f5a6b` | #2 | `e4f5a6b` | 67 | 2 | 69 |
| `003-c7d8e9f` | #3 | `c7d8e9f` | 68 | 1 | 69 |
| `004-f0a1b2c` | #4 | `f0a1b2c` | 69 | 0 | 69 |

## Per-Test Results Across Builds

| Test Case | `001-a1b2c3d` | `002-e4f5a6b` | `003-c7d8e9f` | `004-f0a1b2c` |
|-----------|:---------:|:---------:|:---------:|:---------:|
| `TestWriteThenReadPipeline · test_records_written_to_db_appear_in_api_response` | ✅ | ✅ | ✅ | ✅ |
| `TestWriteThenReadPipeline · test_out_of_bounds_record_excluded_end_to_end` | ✅ | ✅ | ✅ | ✅ |
| `TestWriteThenReadPipeline · test_data_persists_across_connections` | ❌ | ✅ | ✅ | ✅ |
| `TestFilterAccuracyIntegration · test_confidence_high_filter_returns_correct_records` | ✅ | ✅ | ✅ | ✅ |
| `TestFilterAccuracyIntegration · test_confidence_low_filter_returns_correct_records` | ✅ | ✅ | ✅ | ✅ |
| `TestFilterAccuracyIntegration · test_region_ca_filter_excludes_non_california_records` | ✅ | ✅ | ✅ | ✅ |
| `TestFilterAccuracyIntegration · test_combined_region_and_confidence_filter` | ✅ | ✅ | ✅ | ✅ |
| `TestRiskScoringIntegration · test_risk_score_is_computed_for_all_records` | ✅ | ✅ | ✅ | ✅ |
| `TestRiskScoringIntegration · test_risk_score_formula_correctness` | ✅ | ✅ | ✅ | ✅ |
| `TestOrderingIntegration · test_fires_ordered_by_date_desc_then_time_desc` | ❌ | ✅ | ✅ | ✅ |
| `TestFiresEndpointSLA · test_fires_endpoint_responds_under_500ms` | ✅ | ✅ | ✅ | ✅ |
| `TestFiresEndpointSLA · test_fires_region_filter_responds_under_500ms` | ✅ | ✅ | ✅ | ✅ |
| `TestFiresEndpointSLA · test_fires_confidence_filter_responds_under_500ms` | ✅ | ✅ | ✅ | ✅ |
| `TestFiresEndpointSLA · test_fires_combined_filter_responds_under_500ms` | ✅ | ✅ | ✅ | ✅ |
| `TestFiresEndpointSLA · test_fires_endpoint_consistent_across_repeated_calls` | ✅ | ✅ | ✅ | ✅ |
| `TestHealthEndpointSLA · test_health_endpoint_responds_under_100ms` | ✅ | ✅ | ✅ | ✅ |
| `TestHealthEndpointSLA · test_health_endpoint_consistent_across_repeated_calls` | ✅ | ✅ | ❌ | ✅ |
| `TestSQLInjection · test_sql_injection_in_region_param` | ✅ | ✅ | ✅ | ✅ |
| `TestSQLInjection · test_sql_injection_union_in_region_param` | ✅ | ✅ | ✅ | ✅ |
| `TestSQLInjection · test_sql_injection_in_confidence_param` | ✅ | ❌ | ✅ | ✅ |
| `TestSQLInjection · test_table_still_intact_after_injection_attempt` | ✅ | ✅ | ✅ | ✅ |
| `TestXSSProbes · test_xss_script_tag_in_region_param` | ✅ | ✅ | ✅ | ✅ |
| `TestXSSProbes · test_xss_event_handler_in_region_param` | ✅ | ✅ | ✅ | ✅ |
| `TestOversizedInput · test_oversized_region_param_rejected` | ✅ | ✅ | ✅ | ✅ |
| `TestOversizedInput · test_oversized_confidence_param_rejected` | ✅ | ❌ | ✅ | ✅ |
| `TestBoundaryValueAttacks · test_southern_hemisphere_data_excluded` | ✅ | ✅ | ✅ | ✅ |
| `TestBoundaryValueAttacks · test_eastern_hemisphere_data_excluded` | ✅ | ✅ | ✅ | ✅ |
| `TestBoundaryValueAttacks · test_invalid_region_code_rejected` | ✅ | ✅ | ✅ | ✅ |
| `TestInformationDisclosure · test_health_response_returns_expected_fields_only` | ✅ | ✅ | ✅ | ✅ |
| `TestInformationDisclosure · test_400_error_does_not_expose_stack_trace` | ✅ | ✅ | ✅ | ✅ |
| `TestInformationDisclosure · test_confidence_400_error_has_helpful_message` | ✅ | ✅ | ✅ | ✅ |
| `test_root_endpoint` | ✅ | ✅ | ✅ | ✅ |
| `test_health_endpoint` | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_returns_us_data_only` | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_confidence_high` | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_region_ca` | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_region_ca_and_confidence_high` | ✅ | ✅ | ✅ | ✅ |
| `test_invalid_region_returns_400` | ✅ | ✅ | ✅ | ✅ |
| `test_fire_has_expected_fields` | ✅ | ✅ | ✅ | ✅ |
| `test_risk_score_is_numeric` | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_returns_empty_list_when_db_missing` | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_returns_empty_list_when_table_missing` | ✅ | ✅ | ✅ | ✅ |
| `test_api_rejects_invalid_region_parameter` | ✅ | ✅ | ✅ | ✅ |
| `test_api_accepts_valid_region_parameter` | ✅ | ✅ | ✅ | ✅ |
| `test_region_us_returns_only_us_records` | ✅ | ✅ | ✅ | ✅ |
| `test_confidence_filter_with_no_matches_returns_empty_list` | ✅ | ✅ | ✅ | ✅ |
| `test_api_sqli_defense` | ✅ | ✅ | ✅ | ✅ |
| `test_health_check_endpoint` | ✅ | ✅ | ✅ | ✅ |
| `test_compute_risk_logic_boundaries` | ✅ | ✅ | ✅ | ✅ |
| `test_normalize_noaa_hms_with_datetime_column` | ✅ | ✅ | ✅ | ✅ |
| `test_normalize_noaa_hms_with_yearday_column` | ✅ | ✅ | ✅ | ✅ |
| `test_normalize_noaa_hms_filters_out_of_bounds_rows` | ✅ | ✅ | ✅ | ✅ |
| `test_normalize_noaa_hms_requires_lat_lon` | ✅ | ✅ | ✅ | ✅ |
| `test_ingest_noaa_hms_inserts_normalized_rows` | ✅ | ✅ | ✅ | ✅ |
| `test_ingest_noaa_hms_requires_url` | ✅ | ✅ | ✅ | ✅ |
| `TestGetNwsGridpoint · test_returns_tuple_on_success` | ✅ | ✅ | ✅ | ✅ |
| `TestGetNwsGridpoint · test_returns_none_on_api_failure` | ✅ | ✅ | ✅ | ✅ |
| `TestGetNwsGridpoint · test_returns_none_on_malformed_response` | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_mph_to_kmh_conversion` | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_kmh_wind_passthrough` | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_fahrenheit_to_celsius_conversion` | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_humidity_extracted` | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_empty_periods_returns_none` | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_missing_humidity_defaults_to_zero` | ✅ | ✅ | ✅ | ✅ |
| `TestIngestWeather · test_inserts_weather_rows` | ✅ | ✅ | ✅ | ✅ |
| `TestIngestWeather · test_skips_already_fetched_today` | ✅ | ✅ | ✅ | ✅ |
| `TestIngestWeather · test_no_fires_table_returns_zero` | ✅ | ✅ | ✅ | ✅ |
| `TestIngestWeather · test_missing_db_raises` | ✅ | ✅ | ✅ | ✅ |
| `TestIngestWeather · test_offshore_point_skipped` | ✅ | ✅ | ✅ | ✅ |

## Regressions / Fixed Bugs

| Test Case | First Failed Build | Fixed In Build |
|-----------|-------------------|----------------|
| `TestWriteThenReadPipeline · test_data_persists_across_connections` | `001-a1b2c3d` | `002-e4f5a6b` |
| `TestOrderingIntegration · test_fires_ordered_by_date_desc_then_time_desc` | `001-a1b2c3d` | `002-e4f5a6b` |
| `TestHealthEndpointSLA · test_health_endpoint_consistent_across_repeated_calls` | `003-c7d8e9f` | `004-f0a1b2c` |
| `TestSQLInjection · test_sql_injection_in_confidence_param` | `002-e4f5a6b` | `003-c7d8e9f` |
| `TestOversizedInput · test_oversized_confidence_param_rejected` | `002-e4f5a6b` | `003-c7d8e9f` |