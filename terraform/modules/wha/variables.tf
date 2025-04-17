variable "generation" {
  description = "Increment this to force resource recreation"
  type        = number
  default     = 1
}

variable "client_id" {
  description = "Strava client ID"
  type        = string

}

variable "image_version" {
  description = "Docker image version"
  type        = string

}
