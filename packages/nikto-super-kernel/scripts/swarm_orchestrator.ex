# Swarm Orchestrator — Sector 6: Distributed agent coordination (Elixir).
# Standalone BEAM node. Called via subprocess / distributed Erlang.
# Uses GenServer for agent lifecycle and :pg for group membership.

defmodule SwarmOrchestrator do
  use GenServer

  # Client API

  def start_link(opts \\ []) do
    GenServer.start_link(__MODULE__, opts, name: __MODULE__)
  end

  def register_agent(agent_id, role) do
    GenServer.call(__MODULE__, {:register, agent_id, role})
  end

  def dispatch(target, command, payload) do
    GenServer.call(__MODULE__, {:dispatch, target, command, payload})
  end

  def status do
    GenServer.call(__MODULE__, :status)
  end

  # Server callbacks

  def init(_opts) do
    {:ok, %{agents: %{}, tasks: 0}}
  end

  def handle_call({:register, agent_id, role}, _from, state) do
    agents = Map.put(state.agents, agent_id, %{role: role, last_heartbeat: :os.system_time(:second)})
    {:reply, :ok, %{state | agents: agents}}
  end

  def handle_call({:dispatch, target, command, payload}, _from, state) do
    case Map.get(state.agents, target) do
      nil -> {:reply, {:error, :unknown_agent}, state}
      _agent ->
        tasks = state.tasks + 1
        IO.puts("Swarm: dispatched task #{tasks} to #{target}: #{command}")
        {:reply, {:ok, tasks}, %{state | tasks: tasks}}
    end
  end

  def handle_call(:status, _from, state) do
    count = map_size(state.agents)
    {:reply, "Swarm: #{count} agents, #{state.tasks} tasks dispatched", state}
  end
end

# Start the orchestrator when run directly
SwarmOrchestrator.start_link()
IO.puts("SwarmOrchestrator running on #{Node.self()}")
:timer.sleep(:infinity)
