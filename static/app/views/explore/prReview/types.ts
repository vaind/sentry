export interface CodeReviewEvent {
  commentsPosted: number | null;
  dateAdded: string;
  denialReason: string | null;
  githubDeliveryId: string | null;
  githubEventAction: string;
  githubEventType: string;
  id: string;
  organizationId: string;
  prAuthor: string | null;
  prNumber: number | null;
  prTitle: string | null;
  prUrl: string | null;
  repositoryId: string;
  repositoryName: string | null;
  reviewCompletedAt: string | null;
  reviewStartedAt: string | null;
  seerRunId: string | null;
  sentToSeerAt: string | null;
  status: string;
  targetCommitSha: string | null;
  taskEnqueuedAt: string | null;
  trigger: string | null;
  triggerAt: string | null;
  triggerUser: string | null;
  webhookReceivedAt: string | null;
  // Detail-only fields
  comments?: CodeReviewComment[];
  commentsError?: boolean;
  preflightCompletedAt?: string | null;
  reviewResult?: Record<string, unknown> | null;
  timeline?: TimelineEntry[];
}

export interface TimelineEntry {
  stage: string;
  timestamp: string;
}

export interface CodeReviewComment {
  body: string;
  file?: string;
  line?: number;
  runId?: string;
  severity?: string;
}

export interface CodeReviewStats {
  stats: {
    completed: number;
    failed: number;
    preflightDenied: number;
    total: number;
    totalComments: number;
    webhookFiltered: number;
  };
  timeSeries: Array<{
    completed: number;
    count: number;
    date: string;
    failed: number;
  }>;
}
