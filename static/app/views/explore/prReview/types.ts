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
  preflightCompletedAt?: string | null;
}

export interface CodeReviewPR {
  eventCount: number;
  lastActivity: string;
  latestStatus: string;
  latestTrigger: string | null;
  prAuthor: string | null;
  prNumber: number;
  prTitle: string | null;
  prUrl: string | null;
  repositoryId: string;
  repositoryName: string | null;
  totalComments: number;
}

export interface CodeReviewPRDetails {
  comments: CodeReviewComment[];
  commentsError: boolean;
  events: CodeReviewEvent[];
  prAuthor: string | null;
  prNumber: number;
  prTitle: string | null;
  prUrl: string | null;
  repositoryId: string;
  repositoryName: string | null;
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
