import { z } from "zod";

export const UserPublicSchema = z.object({
  id: z.string(),
  email: z.string().email().nullable().optional(),
  username: z.string().nullable().optional(),
});
export type UserPublic = z.infer<typeof UserPublicSchema>;

export const AuthResponseSchema = z.object({
  user: UserPublicSchema,
});
export type AuthResponse = z.infer<typeof AuthResponseSchema>;

export const RunPublicSchema = z.object({
  id: z.string(),
  status: z.string(),
  mode: z.string().optional(),
  roles: z.array(z.string()).nullable().optional(),
  project_id: z.string().nullable().optional(),
  input: z.string(),
  created_at: z.string(),
  started_at: z.string().nullable().optional(),
  finished_at: z.string().nullable().optional(),
});
export type RunPublic = z.infer<typeof RunPublicSchema>;

export const RunDetailSchema = RunPublicSchema.extend({
  output_text: z.string().nullable().optional(),
  error: z.string().nullable().optional(),
});
export type RunDetail = z.infer<typeof RunDetailSchema>;

export const RunListSchema = z.object({
  runs: z.array(RunPublicSchema),
});
export type RunList = z.infer<typeof RunListSchema>;

export const RunEventSchema = z.object({
  seq: z.number().int(),
  type: z.string(),
  message: z.string(),
  data: z.record(z.string(), z.any()).nullable().optional(),
  created_at: z.string(),
});
export type RunEvent = z.infer<typeof RunEventSchema>;

export const RunEventsSchema = z.object({
  events: z.array(RunEventSchema),
});
export type RunEvents = z.infer<typeof RunEventsSchema>;

export const RunCheckpointSchema = z.object({
  seq: z.number().int(),
  node: z.string(),
  state: z.record(z.string(), z.any()),
  created_at: z.string(),
});
export type RunCheckpoint = z.infer<typeof RunCheckpointSchema>;

export const RunCheckpointsSchema = z.object({
  checkpoints: z.array(RunCheckpointSchema),
});
export type RunCheckpoints = z.infer<typeof RunCheckpointsSchema>;

export const ArtifactSchema = z.object({
  id: z.string(),
  name: z.string(),
  mime_type: z.string(),
  created_at: z.string(),
});
export type Artifact = z.infer<typeof ArtifactSchema>;

export const ArtifactDetailSchema = ArtifactSchema.extend({
  content_json: z.record(z.string(), z.any()).nullable().optional(),
  content_text: z.string().nullable().optional(),
});
export type ArtifactDetail = z.infer<typeof ArtifactDetailSchema>;

export const RunArtifactsSchema = z.object({
  artifacts: z.array(ArtifactSchema),
});
export type RunArtifacts = z.infer<typeof RunArtifactsSchema>;

export const ProjectPublicSchema = z.object({
  id: z.string(),
  name: z.string(),
  created_at: z.string(),
});
export type ProjectPublic = z.infer<typeof ProjectPublicSchema>;

export const ProjectListSchema = z.object({
  projects: z.array(ProjectPublicSchema),
});
export type ProjectList = z.infer<typeof ProjectListSchema>;

export const PasswordResetRequestResponseSchema = z.object({
  ok: z.boolean(),
  reset_token: z.string().nullable().optional(),
});
export type PasswordResetRequestResponse = z.infer<
  typeof PasswordResetRequestResponseSchema
>;

export const PasswordResetConfirmResponseSchema = z.object({
  ok: z.boolean(),
});
export type PasswordResetConfirmResponse = z.infer<
  typeof PasswordResetConfirmResponseSchema
>;
