# R Statistical Modeling Wrapper for NIKTO Predictive Engine
# Called from Python via subprocess / rpy2

library(forecast)
library(zoo)

# Read JSON input from stdin and output JSON to stdout
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  writeLines('{"error": "missing_input_file"}')
  quit(status = 1)
}

input_file <- args[1]
if (!file.exists(input_file)) {
  writeLines('{"error": "input_file_not_found"}')
  quit(status = 1)
}

data <- jsonlite::fromJSON(input_file)

compute_arima_forecast <- function(series, steps = 10) {
  ts_data <- ts(series, frequency = 365)
  fit <- auto.arima(ts_data, seasonal = TRUE, stepwise = FALSE, approximation = FALSE)
  fc <- forecast(fit, h = steps)
  result <- list(
    forecast = as.numeric(fc$mean),
    lower_80 = as.numeric(fc$lower[, 1]),
    upper_80 = as.numeric(fc$upper[, 1]),
    lower_95 = as.numeric(fc$lower[, 2]),
    upper_95 = as.numeric(fc$upper[, 2]),
    aic = fit$aic,
    model = paste(fit$arma, collapse = ",")
  )
  return(result)
}

compute_glm_probability <- function(features, outcomes) {
  df <- as.data.frame(cbind(outcomes, features))
  names(df)[1] <- "outcome"
  model <- glm(outcome ~ ., data = df, family = binomial(link = "logit"))
  coefs <- coef(model)
  conf <- confint(model)
  result <- list(
    coefficients = coefs,
    ci_lower = conf[, 1],
    ci_upper = conf[, 2],
    aic = model$aic,
    null_deviance = model$null.deviance,
    residual_deviance = model$deviance
  )
  return(result)
}

compute_bayesian_model <- function(series) {
  # Approximate Bayesian structural time series
  library(CausalImpact)
  # Simple approximation: use pre/post periods
  n <- length(series)
  pre <- series[1:floor(n * 0.8)]
  post <- series[(floor(n * 0.8) + 1):n]
  sd_pre <- sd(pre)
  sd_post <- sd(post)
  result <- list(
    pre_mean = mean(pre),
    post_mean = mean(post),
    pre_sd = sd_pre,
    post_sd = sd_post,
    effect = mean(post) - mean(pre),
    prob_effect = pnorm(0, mean = mean(post) - mean(pre), sd = sqrt(sd_pre^2 + sd_post^2))
  )
  return(result)
}

result <- list()

if (!is.null(data$series)) {
  result$arima <- compute_arima_forecast(data$series, data$steps %||% 10)
}

if (!is.null(data$features) && !is.null(data$outcomes)) {
  result$glm <- compute_glm_probability(data$features, data$outcomes)
}

if (!is.null(data$bayesian_series)) {
  result$bayesian <- compute_bayesian_model(data$bayesian_series)
}

writeLines(jsonlite::toJSON(result, auto_unbox = TRUE))
