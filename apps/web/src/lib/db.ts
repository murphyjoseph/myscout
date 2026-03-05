import { Pool } from "pg";

// LOCAL-ONLY: Hardcoded credentials are fine here — this never leaves your
// machine. In a production app you'd use a secrets manager and never
// expose DB credentials in source code.
const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL ||
    "postgresql://myscout:myscout@localhost:5432/myscout",
});

export async function query<T = Record<string, unknown>>(
  text: string,
  params?: unknown[]
): Promise<T[]> {
  const result = await pool.query(text, params);
  return result.rows as T[];
}

export default pool;
