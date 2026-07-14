import { drizzle } from 'drizzle-orm/node-postgres';
import pkg from 'pg';
const { Pool } = pkg;
import * as schema from './schema.ts';

export const createPool = () => {
  return new Pool({
    host: process.env.SQL_HOST,
    user: process.env.SQL_USER,
    password: process.env.SQL_PASSWORD,
    database: process.env.SQL_DB_NAME,
    connectionTimeoutMillis: 15000,
  });
};

const isSqlConfigured = !!process.env.SQL_HOST;

let db: any;

if (isSqlConfigured) {
  const pool = createPool();
  pool.on('error', (err) => {
    console.error('Unexpected error on idle SQL pool client:', err);
  });
  db = drizzle(pool, { schema });
} else {
  console.warn('[AI Studio] SQL database not configured (SQL_HOST missing) — using in-memory mock database');
  
  // In-memory tables
  const mockUsers: any[] = [];
  const mockRlMemory: any[] = [];
  const mockGameHistory: any[] = [];
  
  let userIdCounter = 1;
  let rlMemoryIdCounter = 1;
  let gameHistoryIdCounter = 1;
  
  const evaluateCondition = (item: any, condition: any) => {
    if (!condition) return true;
    if (condition.left && condition.right !== undefined) {
      const colName = condition.left.name;
      const val = condition.right;
      
      let propName = colName;
      if (colName === 'user_id') propName = 'userId';
      if (colName === 'password_hash') propName = 'passwordHash';
      if (colName === 'real_email') propName = 'realEmail';
      if (colName === 'created_at') propName = 'createdAt';
      if (colName === 'updated_at') propName = 'updatedAt';
      
      return item[propName] === val;
    }
    return true;
  };
  
  db = {
    select: () => {
      return {
        from: (table: any) => {
          const tableName = table?.['_']?.name || table?.name;
          const data = tableName === 'users' ? mockUsers : tableName === 'rl_memory' ? mockRlMemory : mockGameHistory;
          
          return {
            where: (condition: any) => {
              const filtered = data.filter(item => evaluateCondition(item, condition));
              return {
                then: (resolve: any) => resolve(filtered)
              };
            },
            then: (resolve: any) => resolve(data)
          };
        }
      };
    },
    insert: (table: any) => {
      const tableName = table?.['_']?.name || table?.name;
      return {
        values: (valuesObj: any) => {
          const runInsert = () => {
            if (tableName === 'users') {
              const existingIndex = mockUsers.findIndex(u => u.uid === valuesObj.uid);
              if (existingIndex !== -1) {
                mockUsers[existingIndex] = { ...mockUsers[existingIndex], ...valuesObj };
                return [mockUsers[existingIndex]];
              }
              const newUser = { id: userIdCounter++, ...valuesObj, createdAt: new Date() };
              mockUsers.push(newUser);
              return [newUser];
            } else if (tableName === 'rl_memory') {
              const existingIndex = mockRlMemory.findIndex(r => r.userId === valuesObj.userId);
              if (existingIndex !== -1) {
                mockRlMemory[existingIndex] = { ...mockRlMemory[existingIndex], ...valuesObj, updatedAt: new Date() };
                return [mockRlMemory[existingIndex]];
              }
              const newRl = { id: rlMemoryIdCounter++, ...valuesObj, updatedAt: new Date() };
              mockRlMemory.push(newRl);
              return [newRl];
            } else {
              const newHistory = { id: gameHistoryIdCounter++, ...valuesObj, updatedAt: new Date() };
              mockGameHistory.push(newHistory);
              return [newHistory];
            }
          };

          return {
            onConflictDoUpdate: (conflictObj: any) => {
              return {
                returning: () => ({
                  then: (resolve: any) => resolve(runInsert())
                }),
                then: (resolve: any) => resolve(runInsert())
              };
            },
            returning: () => ({
              then: (resolve: any) => resolve(runInsert())
            }),
            then: (resolve: any) => resolve(runInsert())
          };
        }
      };
    }
  };
}

export { db };
