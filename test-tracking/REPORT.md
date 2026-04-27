# Test Result History

**Builds tracked:** 5  |  **Test cases tracked:** 109

## Build Summary

| Build ID | Run | SHA | Passed | Failed | Total |
|----------|-----|-----|--------|--------|-------|
| `005-4325232` | #? | `4325232` | 108 | 0 | 108 |
| `001-a1b2c3d` | #1 | `a1b2c3d` | 67 | 2 | 69 |
| `002-e4f5a6b` | #2 | `e4f5a6b` | 67 | 2 | 69 |
| `003-c7d8e9f` | #3 | `c7d8e9f` | 68 | 1 | 69 |
| `004-f0a1b2c` | #4 | `f0a1b2c` | 69 | 0 | 69 |

## Per-Test Results Across Builds

| Test Case | `005-4325232` | `001-a1b2c3d` | `002-e4f5a6b` | `003-c7d8e9f` | `004-f0a1b2c` |
|-----------|:---------:|:---------:|:---------:|:---------:|:---------:|
| `TestWriteThenReadPipeline · test_records_written_to_db_appear_in_api_response` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestWriteThenReadPipeline · test_out_of_bounds_record_excluded_end_to_end` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestWriteThenReadPipeline · test_data_persists_across_connections` | ✅ | ❌ | ✅ | ✅ | ✅ |
| `TestFilterAccuracyIntegration · test_confidence_high_filter_returns_correct_records` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestFilterAccuracyIntegration · test_confidence_low_filter_returns_correct_records` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestFilterAccuracyIntegration · test_region_ca_filter_excludes_non_california_records` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestFilterAccuracyIntegration · test_combined_region_and_confidence_filter` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestRiskScoringIntegration · test_risk_score_is_computed_for_all_records` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestRiskScoringIntegration · test_risk_score_formula_correctness` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestOrderingIntegration · test_fires_ordered_by_date_desc_then_time_desc` | ✅ | ❌ | ✅ | ✅ | ✅ |
| `TestFiresEndpointSLA · test_fires_endpoint_responds_under_500ms` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestFiresEndpointSLA · test_fires_region_filter_responds_under_500ms` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestFiresEndpointSLA · test_fires_confidence_filter_responds_under_500ms` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestFiresEndpointSLA · test_fires_combined_filter_responds_under_500ms` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestFiresEndpointSLA · test_fires_endpoint_consistent_across_repeated_calls` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestHealthEndpointSLA · test_health_endpoint_responds_under_100ms` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestHealthEndpointSLA · test_health_endpoint_consistent_across_repeated_calls` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `TestSQLInjection · test_sql_injection_in_region_param` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestSQLInjection · test_sql_injection_union_in_region_param` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestSQLInjection · test_sql_injection_in_confidence_param` | ✅ | ✅ | ❌ | ✅ | ✅ |
| `TestSQLInjection · test_table_still_intact_after_injection_attempt` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestXSSProbes · test_xss_script_tag_in_region_param` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestXSSProbes · test_xss_event_handler_in_region_param` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestOversizedInput · test_oversized_region_param_rejected` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestOversizedInput · test_oversized_confidence_param_rejected` | ✅ | ✅ | ❌ | ✅ | ✅ |
| `TestBoundaryValueAttacks · test_southern_hemisphere_data_excluded` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestBoundaryValueAttacks · test_eastern_hemisphere_data_excluded` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestBoundaryValueAttacks · test_invalid_region_code_rejected` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestInformationDisclosure · test_health_response_returns_expected_fields_only` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestInformationDisclosure · test_400_error_does_not_expose_stack_trace` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestInformationDisclosure · test_confidence_400_error_has_helpful_message` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_root_endpoint` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_health_endpoint` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_returns_us_data_only` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_confidence_high` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_region_ca` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_region_ca_and_confidence_high` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_invalid_region_returns_400` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_fire_has_expected_fields` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_risk_score_is_numeric` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_returns_empty_list_when_db_missing` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_get_fires_returns_empty_list_when_table_missing` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_api_rejects_invalid_region_parameter` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_api_accepts_valid_region_parameter` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_region_us_returns_only_us_records` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_confidence_filter_with_no_matches_returns_empty_list` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_api_sqli_defense` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_health_check_endpoint` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_fallback_risk_returns_normalized_score` | ✅ | — | — | — | — |
| `test_get_fires_confidence_low_returns_matching_record` | ✅ | — | — | — | — |
| `test_get_fires_region_ca_and_confidence_low_returns_matching_record` | ✅ | — | — | — | — |
| `test_get_fires_invalid_confidence_returns_400` | ✅ | — | — | — | — |
| `test_fire_values_have_expected_types` | ✅ | — | — | — | — |
| `test_fires_are_sorted_newest_first` | ✅ | — | — | — | — |
| `test_health_endpoint_db_exists_true` | ✅ | — | — | — | — |
| `test_health_endpoint_has_expected_types` | ✅ | — | — | — | — |
| `test_ensure_fires_table_creates_table` | ✅ | — | — | — | — |
| `test_ingest_firms_requires_api_key` | ✅ | — | — | — | — |
| `test_ingest_firms_inserts_only_us_rows` | ✅ | — | — | — | — |
| `test_ingest_firms_deduplicates_on_repeated_run` | ✅ | — | — | — | — |
| `test_ingest_firms_empty_us_result_creates_table_with_no_rows` | ✅ | — | — | — | — |
| `test_normalize_noaa_hms_with_datetime_column` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_normalize_noaa_hms_with_yearday_column` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_normalize_noaa_hms_filters_out_of_bounds_rows` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_normalize_noaa_hms_requires_lat_lon` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_ingest_noaa_hms_inserts_normalized_rows` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_ingest_noaa_hms_deduplicates_on_repeated_run` | ✅ | — | — | — | — |
| `test_ingest_noaa_hms_requires_url` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestMetricsEndpoint · test_metrics_endpoint_returns_200` | ✅ | — | — | — | — |
| `TestMetricsEndpoint · test_metrics_has_required_fields` | ✅ | — | — | — | — |
| `TestMetricsEndpoint · test_request_counts_tracks_fires_and_health` | ✅ | — | — | — | — |
| `TestMetricsEndpoint · test_fires_counter_increments_after_fires_request` | ✅ | — | — | — | — |
| `TestMetricsEndpoint · test_last_fires_response_ms_populated_after_fires_call` | ✅ | — | — | — | — |
| `TestMetricsEndpoint · test_uptime_seconds_is_non_negative_float` | ✅ | — | — | — | — |
| `TestFetchEnvironmentalConditions · test_tc07_returns_correct_values_on_success` | ✅ | — | — | — | — |
| `TestFetchEnvironmentalConditions · test_tc08_returns_none_on_request_failure` | ✅ | — | — | — | — |
| `TestFetchEnvironmentalConditions · test_tc09_null_values_default_to_zero` | ✅ | — | — | — | — |
| `TestFetchEnvironmentalConditions · test_returns_none_on_missing_keys` | ✅ | — | — | — | — |
| `TestFetchEnvironmentalConditions · test_soil_moisture_is_mean_of_hourly_values` | ✅ | — | — | — | — |
| `TestAlreadyFetchedToday · test_returns_false_when_table_empty` | ✅ | — | — | — | — |
| `TestAlreadyFetchedToday · test_returns_true_when_row_exists` | ✅ | — | — | — | — |
| `TestIngestEnvironmental · test_tc10_inserts_rows_for_all_fire_points` | ✅ | — | — | — | — |
| `TestIngestEnvironmental · test_tc11_skips_already_fetched_point` | ✅ | — | — | — | — |
| `TestIngestEnvironmental · test_tc12_no_fires_table_returns_zero` | ✅ | — | — | — | — |
| `TestIngestEnvironmental · test_tc13_missing_db_raises` | ✅ | — | — | — | — |
| `TestIngestEnvironmental · test_tc14_api_failure_skips_all_points` | ✅ | — | — | — | — |
| `test_fires_endpoint_returns_within_one_second` | ✅ | — | — | — | — |
| `test_fires_endpoint_region_filter_returns_within_one_second` | ✅ | — | — | — | — |
| `test_fires_endpoint_confidence_filter_returns_within_one_second` | ✅ | — | — | — | — |
| `test_fallback_risk_increases_with_brightness` | ✅ | — | — | — | — |
| `test_fallback_risk_increases_with_frp` | ✅ | — | — | — | — |
| `test_fallback_risk_ranks_severe_fire_higher_than_mild` | ✅ | — | — | — | — |
| `test_fallback_risk_same_inputs_same_score` | ✅ | — | — | — | — |
| `test_fallback_risk_handles_missing_values` | ✅ | — | — | — | — |
| `TestGetNwsGridpoint · test_returns_tuple_on_success` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestGetNwsGridpoint · test_returns_none_on_api_failure` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestGetNwsGridpoint · test_returns_none_on_malformed_response` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_mph_to_kmh_conversion` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_kmh_wind_passthrough` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_fahrenheit_to_celsius_conversion` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_humidity_extracted` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_empty_periods_returns_none` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestExtractCurrentConditions · test_missing_humidity_defaults_to_zero` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestIngestWeather · test_inserts_weather_rows` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestIngestWeather · test_skips_already_fetched_today` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestIngestWeather · test_no_fires_table_returns_zero` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestIngestWeather · test_missing_db_raises` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `TestIngestWeather · test_offshore_point_skipped` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test_compute_risk_logic_boundaries` | — | ✅ | ✅ | ✅ | ✅ |

## Regressions / Fixed Bugs

| Test Case | First Failed Build | Fixed In Build |
|-----------|-------------------|----------------|
| `TestWriteThenReadPipeline · test_data_persists_across_connections` | `001-a1b2c3d` | `002-e4f5a6b` |
| `TestOrderingIntegration · test_fires_ordered_by_date_desc_then_time_desc` | `001-a1b2c3d` | `002-e4f5a6b` |
| `TestHealthEndpointSLA · test_health_endpoint_consistent_across_repeated_calls` | `003-c7d8e9f` | `004-f0a1b2c` |
| `TestSQLInjection · test_sql_injection_in_confidence_param` | `002-e4f5a6b` | `003-c7d8e9f` |
| `TestOversizedInput · test_oversized_confidence_param_rejected` | `002-e4f5a6b` | `003-c7d8e9f` |