variable "aws_region" {
  type    = string
  default = "us-west-1"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "project_name" {
  type    = string
  default = "alfred"
}

variable "runtime" {
  type    = string
  default = "python3.13"
}
