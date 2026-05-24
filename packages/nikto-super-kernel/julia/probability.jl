# Julia Probability Modeling for NIKTO Predictive Engine
# Called from Python via subprocess / JuliaCall

using Distributions
using Turing
using JSON
using Random

# Read input from a file path argument
input_path = ARGS[1]
input_data = JSON.parsefile(input_path)

function monte_carlo_probability(mean_rating, std_rating, n_simulations)
    dist = Normal(mean_rating, std_rating)
    samples = rand(dist, n_simulations)
    return Dict(
        "mean" => mean(samples),
        "std" => std(samples),
        "percentile_5" => quantile(samples, 0.05),
        "percentile_25" => quantile(samples, 0.25),
        "percentile_75" => quantile(samples, 0.75),
        "percentile_95" => quantile(samples, 0.95),
        "prob_positive" => count(x -> x > 0, samples) / n_simulations
    )
end

function bayesian_elo_update(team_a_rating, team_b_rating, result_obs, n_samples)
    @model function elo_model(ra, rb, result)
        σ ~ InverseGamma(10, 10)  # rating volatility
        skill_a ~ Normal(ra, σ)
        skill_b ~ Normal(rb, σ)
        logit_p = skill_a - skill_b
        result ~ BernoulliLogit(logit_p)
    end
    model = elo_model(team_a_rating, team_b_rating, result_obs)
    chain = sample(model, NUTS(), n_samples)
    return Dict(
        "skill_a_mean" => mean(chain[:skill_a]),
        "skill_b_mean" => mean(chain[:skill_b]),
        "sigma" => mean(chain[:σ]),
        "prob_a_wins" => mean(chain[:skill_a] .> chain[:skill_b])
    )
end

function compute_markov_transition(series, n_states)
    n = length(series)
    min_val = minimum(series)
    max_val = maximum(series)
    step = (max_val - min_val) / n_states
    if step == 0 step = 1 end
    states = min.(floor.(Int, (series .- min_val) ./ step) .+ 1, n_states)
    transition = zeros(Int, n_states, n_states)
    for i in 1:(n - 1)
        transition[states[i], states[i + 1]] += 1
    end
    probs = transition ./ max.(sum(transition, dims=2), 1)
    return Dict(
        "n_states" => n_states,
        "transition_matrix" => probs,
        "steady_state" => eigvecs(probs')[:, 1] ./ sum(eigvecs(probs')[:, 1])
    )
end

result = Dict()

if haskey(input_data, "ratings")
    result["monte_carlo"] = monte_carlo_probability(
        input_data["ratings"]["mean"],
        input_data["ratings"]["std"],
        get(input_data, "n_simulations", 100000)
    )
end

if haskey(input_data, "elo_update")
    e = input_data["elo_update"]
    result["bayesian_elo"] = bayesian_elo_update(
        e["team_a_rating"],
        e["team_b_rating"],
        e["result"],
        get(input_data, "n_samples", 1000)
    )
end

if haskey(input_data, "series")
    result["markov"] = compute_markov_transition(
        input_data["series"],
        get(input_data, "n_states", 5)
    )
end

println(JSON.json(result))
