import { writeFileSync, readFileSync, existsSync, mkdirSync } from "fs"
import { join } from "path"

const STATS_FILE = join(process.env.HOME || "", ".cache", "opencode", "prompt-stats.json")

function loadStats() {
  try {
    if (existsSync(STATS_FILE)) {
      return JSON.parse(readFileSync(STATS_FILE, "utf-8"))
    }
  } catch {}
  return { 
    total: 0, 
    bySession: {}, 
    byModel: {}, 
    byAgent: {},
    history: [] 
  }
}

function saveStats(stats) {
  const dir = join(process.env.HOME || "", ".cache", "opencode")
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
  writeFileSync(STATS_FILE, JSON.stringify(stats, null, 2))
}

export const PromptTrackerPlugin = async ({ client }) => {
  let stats = loadStats()

  return {
    "session.created": async (input, output) => {
      const sessionId = output.session?.id || "unknown"
      stats.bySession[sessionId] = { count: 0, model: null, agent: null }
      saveStats(stats)
    },

    "session.updated": async (input, output) => {
      const sessionId = output.session?.id || input.sessionId
      if (sessionId && stats.bySession[sessionId]) {
        stats.bySession[sessionId].count++
        if (output.session?.model) {
          stats.bySession[sessionId].model = output.session.model
        }
        if (output.session?.agent) {
          stats.bySession[sessionId].agent = output.session.agent
        }
      }
      saveStats(stats)
    },

    "message.updated": async (input, output) => {
      if (output.message?.role === "user") {
        stats.total++
        const model = output.message?.model || "unknown"
        const agent = output.message?.agent || "unknown"
        
        stats.byModel[model] = (stats.byModel[model] || 0) + 1
        stats.byAgent[agent] = (stats.byAgent[agent] || 0) + 1
        
        stats.history.push({
          timestamp: new Date().toISOString(),
          model,
          agent,
        })
        
        // Keep only last 1000 entries
        if (stats.history.length > 1000) {
          stats.history = stats.history.slice(-1000)
        }
        
        saveStats(stats)
      }
    },

    "tui.command.execute": async (input, output) => {
      if (output.command === "/stats" || output.command === "/prompt-stats") {
        console.log("\n📊 Prompt Statistics")
        console.log("═".repeat(40))
        console.log(`Total Prompts: ${stats.total}`)
        console.log("\n📈 By Model:")
        Object.entries(stats.byModel).forEach(([model, count]) => {
          console.log(`  ${model}: ${count}`)
        })
        console.log("\n🤖 By Agent:")
        Object.entries(stats.byAgent).forEach(([agent, count]) => {
          console.log(`  ${agent}: ${count}`)
        })
        console.log("═".repeat(40))
      }
    },
  }
}
