data "aws_caller_identity" "current" {}

locals {
  github_repo           = "${var.github_owner}/${var.github_repository}"
  oidc_provider_url     = "https://token.actions.githubusercontent.com"
  oidc_provider_host    = "token.actions.githubusercontent.com"
  state_object_arn      = "arn:aws:s3:::${var.state_bucket_name}/${var.state_key}"
  state_lockfile_arn    = "arn:aws:s3:::${var.state_bucket_name}/${var.state_key}.tflock"
  state_bucket_arn      = "arn:aws:s3:::${var.state_bucket_name}"
  plan_role_name        = "${var.role_name_prefix}-Plan"
  apply_role_name       = "${var.role_name_prefix}-Apply"
  plan_environment_sub  = "repo:${local.github_repo}:environment:${var.github_plan_environment}"
  apply_environment_sub = "repo:${local.github_repo}:environment:${var.github_apply_environment}"
}

resource "aws_iam_openid_connect_provider" "github" {
  url = local.oidc_provider_url

  client_id_list = [
    "sts.amazonaws.com",
  ]

  tags = merge(var.tags, {
    Name = "github-actions-oidc"
  })
}

data "aws_iam_policy_document" "plan_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_host}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_host}:sub"
      values   = [local.plan_environment_sub]
    }
  }
}

data "aws_iam_policy_document" "apply_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_host}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_host}:sub"
      values   = [local.apply_environment_sub]
    }
  }
}

resource "aws_iam_role" "plan" {
  name               = local.plan_role_name
  assume_role_policy = data.aws_iam_policy_document.plan_trust.json
  description        = "GitHub Actions role for Terraform plan in ${local.github_repo}."

  tags = merge(var.tags, {
    Name = local.plan_role_name
  })
}

resource "aws_iam_role" "apply" {
  name               = local.apply_role_name
  assume_role_policy = data.aws_iam_policy_document.apply_trust.json
  description        = "GitHub Actions role reserved for future Terraform apply in ${local.github_repo}."

  tags = merge(var.tags, {
    Name = local.apply_role_name
  })
}

data "aws_iam_policy_document" "state_access" {
  statement {
    sid       = "ListStatePrefix"
    actions   = ["s3:ListBucket"]
    resources = [local.state_bucket_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        var.state_key,
        "${var.state_key}.tflock",
      ]
    }
  }

  statement {
    sid = "ReadWriteState"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [local.state_object_arn]
  }

  statement {
    sid = "ReadWriteDeleteLockfile"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [local.state_lockfile_arn]
  }
}

resource "aws_iam_policy" "state_access" {
  name        = "${var.role_name_prefix}-StateAccess"
  description = "Allow Terraform roles to access S3 state and native S3 lockfiles."
  policy      = data.aws_iam_policy_document.state_access.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "plan_state_access" {
  role       = aws_iam_role.plan.name
  policy_arn = aws_iam_policy.state_access.arn
}

resource "aws_iam_role_policy_attachment" "apply_state_access" {
  role       = aws_iam_role.apply.name
  policy_arn = aws_iam_policy.state_access.arn
}

resource "aws_iam_role_policy_attachment" "plan_read_only" {
  role       = aws_iam_role.plan.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "apply_managed" {
  for_each = toset(var.apply_role_managed_policy_arns)

  role       = aws_iam_role.apply.name
  policy_arn = each.value
}
