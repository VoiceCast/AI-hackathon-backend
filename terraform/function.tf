resource "google_cloudfunctions2_function" "manzai_multi_agent" {
  name        = "multi_agent"
  location    = var.region
  runtime     = "python310" # 適切なPythonランタイムを指定
  entry_point = "hello_world"

  # ソースコードの設定（Cloud Storageを使用）
  build_config {
    runtime     = "python310"
    entry_point = "hello_world"
    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    timeout_seconds   = 60
    available_memory  = "256M"
    min_instance_count = 1
    max_instance_count = 3
  }

  trigger_config {
    trigger_type = "HTTP"
  }
}
