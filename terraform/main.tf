provider "aws" {
  region = var.region
}

data "aws_ami" "ami" {
  owners = [
    "amazon"]
  most_recent = true
  name_regex = "amazon*"
}

resource "aws_s3_bucket" "b" {
  bucket = "my-tf-test-bucket-pinnaka"
  acl    = "private"
}

output "wehat-web-have"{
  value = [for x in var.prefixes: x[0]]
}

terraform {
  backend "remote" {
    organization = "pinnaka"

    workspaces {
      name = "training"
    }
  }
}

variable "region" {
  default = "us-east-1"
}

variable "env" {
  default = "test"
}

variable "tags" {
  default = ""
}

variable "prefixes" {
  default = []
}