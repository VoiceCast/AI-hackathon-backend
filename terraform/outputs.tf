output "function_url" {
  description = "The HTTP endpoint of the deployed Cloud Function"
  value       = google_cloudfunctions2_function.manzai_multi_agent.service_config[0].uri
}
