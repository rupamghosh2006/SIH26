import { spawn } from "child_process"
import { existsSync } from "fs"

export interface PythonResult {
  stdout: string
  stderr: string
  code: number
}

function resolvePythonPath(): string {
  if (process.env.PYTHON_EXEC && existsSync(process.env.PYTHON_EXEC)) {
    return process.env.PYTHON_EXEC
  }
  
  if (process.platform === "win32") {
    const knownPaths = [
      "C:\\Program Files\\Python313\\python.exe",
      "C:\\Program Files\\Python312\\python.exe",
      "C:\\Program Files\\Python311\\python.exe",
      "C:\\Program Files\\Python310\\python.exe",
      "C:\\Python313\\python.exe",
      "C:\\Python312\\python.exe",
      "C:\\Python311\\python.exe"
    ]
    for (const p of knownPaths) {
      if (existsSync(p)) return p
    }
  }
  
  return process.platform === "win32" ? "python" : "python3"
}

export async function runPythonCommand(
  args: string[], 
  cwd: string,
  timeoutMs: number = 35000
): Promise<PythonResult> {
  return new Promise<PythonResult>((resolve) => {
    const py = resolvePythonPath()
    let stdout = ""
    let stderr = ""
    let settled = false

    const child = spawn(py, args, { 
      cwd,
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1"
      }
    })

    const timer = setTimeout(() => {
      if (!settled) {
        settled = true
        try { child.kill() } catch (_) {}
        resolve({
          stdout,
          stderr: stderr + "\nExecution timed out",
          code: 124
        })
      }
    }, timeoutMs)

    child.stdout.on("data", (data) => {
      stdout += data.toString()
    })

    child.stderr.on("data", (data) => {
      stderr += data.toString()
    })

    child.on("close", (code) => {
      if (!settled) {
        settled = true
        clearTimeout(timer)
        resolve({
          stdout,
          stderr,
          code: code ?? 0
        })
      }
    })

    child.on("error", (error) => {
      if (!settled) {
        settled = true
        clearTimeout(timer)
        resolve({
          stdout,
          stderr: stderr + "\n" + error.message,
          code: 1
        })
      }
    })
  })
}
