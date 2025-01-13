# Cloud Storage バケットの定義
resource "manzai_multi_agentstorage_bucket" "function_bucket" {
  name          = "manzai-multi-agent-bucket-${random_id.bucket_suffix.hex}"
  location      = "US"
  force_destroy = true # バケット削除時に中身も削除
  uniform_bucket_level_access = true
}

# バケット名の一意性を確保するためのランダムID
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# ソースコードを保存するオブジェクト
resource "google_storage_bucket_object" "function_source" {
  name   = "function-source.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = "${path.module}/../functions/manzai_multi_agent.zip" # ソースZIPのローカルパス
}
