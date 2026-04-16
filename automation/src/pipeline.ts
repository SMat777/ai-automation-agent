/**
 * Pipeline — Orchestrates a sequence of named steps with error handling.
 *
 * Each step receives the output of the previous step as input.
 * Tracks timing, step count, and provides a structured result.
 */

type StepHandler = (input: unknown) => unknown | Promise<unknown>;

interface PipelineStep {
  name: string;
  handler: StepHandler;
}

/** Result metadata from a pipeline execution */
export interface PipelineResult {
  output: unknown;
  pipelineName: string;
  stepCount: number;
  totalDurationMs: number;
  steps: { name: string; durationMs: number }[];
}

export class Pipeline {
  private steps: PipelineStep[] = [];
  private name: string;

  constructor(name: string) {
    this.name = name;
  }

  /**
   * Add a step to the pipeline.
   * Returns `this` for chaining: pipeline.step(...).step(...).execute()
   */
  step(name: string, handler: StepHandler): this {
    this.steps.push({ name, handler });
    return this;
  }

  /**
   * Execute all steps in sequence, passing each result to the next step.
   * Returns a structured result with output and metadata.
   */
  async execute(initialInput?: unknown): Promise<PipelineResult> {
    const pipelineStart = Date.now();
    const stepResults: { name: string; durationMs: number }[] = [];

    console.log(`Pipeline: ${this.name}`);
    console.log(`Steps: ${this.steps.length}`);
    console.log("─".repeat(40));

    let current: unknown = initialInput;

    for (const [index, step] of this.steps.entries()) {
      const stepNumber = index + 1;
      console.log(`\n[${stepNumber}/${this.steps.length}] ${step.name}...`);

      const start = Date.now();

      try {
        current = await step.handler(current);
      } catch (error) {
        const duration = Date.now() - start;
        console.log(`  ✗ Failed (${duration}ms)`);
        throw new PipelineError(
          `Step "${step.name}" failed: ${error instanceof Error ? error.message : String(error)}`,
          step.name,
          stepNumber,
          error instanceof Error ? error : undefined,
        );
      }

      const duration = Date.now() - start;
      stepResults.push({ name: step.name, durationMs: duration });
      console.log(`  ✓ Done (${duration}ms)`);
    }

    const totalDuration = Date.now() - pipelineStart;

    return {
      output: current,
      pipelineName: this.name,
      stepCount: this.steps.length,
      totalDurationMs: totalDuration,
      steps: stepResults,
    };
  }
}

/** Structured error for pipeline failures */
export class PipelineError extends Error {
  constructor(
    message: string,
    public readonly stepName: string,
    public readonly stepNumber: number,
    public readonly cause?: Error,
  ) {
    super(message);
    this.name = "PipelineError";
  }
}
