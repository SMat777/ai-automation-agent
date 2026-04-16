/**
 * Pipeline — Orchestrates a sequence of named steps.
 *
 * Each step receives the output of the previous step as input.
 * Steps are defined with a name (for logging) and a handler function.
 */

type StepHandler = (input: unknown) => unknown | Promise<unknown>;

interface PipelineStep {
  name: string;
  handler: StepHandler;
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
   */
  async execute(initialInput?: unknown): Promise<unknown> {
    console.log(`Pipeline: ${this.name}`);
    console.log(`Steps: ${this.steps.length}`);
    console.log("─".repeat(40));

    let current: unknown = initialInput;

    for (const [index, step] of this.steps.entries()) {
      const stepNumber = index + 1;
      console.log(`\n[${stepNumber}/${this.steps.length}] ${step.name}...`);

      const start = Date.now();
      current = await step.handler(current);
      const duration = Date.now() - start;

      console.log(`  ✓ Done (${duration}ms)`);
    }

    return current;
  }
}
