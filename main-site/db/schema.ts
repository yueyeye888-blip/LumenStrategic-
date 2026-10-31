import { sqliteTable, text } from "drizzle-orm/sqlite-core";
export const applications=sqliteTable("applications",{
 id:text("id").primaryKey(),
 name:text("name").notNull(),
 email:text("email").notNull(),
 investorType:text("investor_type").notNull(),
 topic:text("topic").notNull(),
 size:text("investment_size").notNull(),
 message:text("message").notNull(),
 language:text("language").notNull(),
 createdAt:text("created_at").notNull(),
});
