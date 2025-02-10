# Cloud Storage バケットの定義
resource "google_storage_bucket" "function_bucket_multi_agent" {
  name          = "manzai-multi-agent-bucket-${random_id.bucket_suffix.hex}"
  location      = "ASIA-NORTHEAST1"
  force_destroy = true # バケット削除時に中身も削除
  uniform_bucket_level_access = true
}

# バケット名の一意性を確保するためのランダムID
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# ソースコードを保存するオブジェクト
resource "google_storage_bucket_object" "function_source_multi_agent" {
  name   = "function-source.zip"
  bucket = google_storage_bucket.function_bucket_multi_agent.name
  source = "${path.module}/../functions/manzai_multi_agent/manzai_multi_agent.zip" # ソースZIPのローカルパス
}

# Cloud Storage バケットの定義
resource "google_storage_bucket" "function_bucket_theme_generator" {
  name          = "manzai-theme-generator-bucket-${random_id.bucket_suffix.hex}"
  location      = "ASIA-NORTHEAST1"
  force_destroy = true # バケット削除時に中身も削除
  uniform_bucket_level_access = true
}

# ソースコードを保存するオブジェクト
resource "google_storage_bucket_object" "function_source_theme_generator" {
  name   = "function-source.zip"
  bucket = google_storage_bucket.function_bucket_theme_generator.name
  source = "${path.module}/../functions/manzai_theme_generator/manzai_theme_generator.zip" # ソースZIPのローカルパス
}
