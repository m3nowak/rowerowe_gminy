variable "es_access_id" {
  type      = string
  sensitive = true

}
variable "es_access_type" {
  type      = string
  sensitive = true
}
variable "es_access_type_param" {
  type      = string
  sensitive = true
}

variable "client_id" {
  description = "Strava client ID"
  type        = string

}

variable "image_version" {
  description = "Docker image version"
  type        = string

}
