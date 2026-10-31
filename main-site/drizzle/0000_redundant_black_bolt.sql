CREATE TABLE `applications` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`email` text NOT NULL,
	`investor_type` text NOT NULL,
	`topic` text NOT NULL,
	`investment_size` text NOT NULL,
	`message` text NOT NULL,
	`language` text NOT NULL,
	`created_at` text NOT NULL
);
