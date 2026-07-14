// src/db/schema.ts
import { relations } from 'drizzle-orm';
import { integer, pgTable, serial, text, timestamp, jsonb } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  uid: text('uid').notNull().unique(), // Firebase Auth UID
  email: text('email').notNull(),
  passwordHash: text('password_hash'),
  realEmail: text('real_email'),
  createdAt: timestamp('created_at').defaultNow(),
});

export const rlMemory = pgTable('rl_memory', {
  id: serial('id').primaryKey(),
  userId: integer('user_id').references(() => users.id).notNull(),
  gamesPlayed: integer('games_played').default(0),
  botWins: integer('bot_wins').default(0),
  botLosses: integer('bot_losses').default(0),
  botDraws: integer('bot_draws').default(0),
  qTable: jsonb('q_table').default({}),
  recentLearnings: jsonb('recent_learnings').default([]),
  updatedAt: timestamp('updated_at').defaultNow(),
});

export const gameHistory = pgTable('game_history', {
  id: serial('id').primaryKey(),
  userId: integer('user_id').references(() => users.id).notNull(),
  historyData: jsonb('history_data').notNull(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

export const usersRelations = relations(users, ({ many }) => ({
  rlMemory: many(rlMemory),
  gameHistory: many(gameHistory),
}));
