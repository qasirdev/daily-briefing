"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

type BriefingErrorBoundaryProps = {
  children: ReactNode;
  onReset?: () => void;
};

type BriefingErrorBoundaryState = {
  hasError: boolean;
  error: Error | null;
};

function BriefingFallback({
  error,
  onReset,
}: {
  error: Error | null;
  onReset: () => void;
}) {
  return (
    <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-700 dark:bg-red-950/40">
      <h2 className="text-lg font-semibold text-red-800 dark:text-red-100">Something went wrong</h2>
      <p className="mt-1 text-sm text-red-600 dark:text-red-200">
        {error?.message ?? "The briefing view failed to render."}
      </p>
      <button
        type="button"
        className="mt-3 rounded-md bg-red-800 px-3 py-1.5 text-sm text-white hover:bg-red-900"
        onClick={onReset}
      >
        Try again
      </button>
    </div>
  );
}

export class BriefingErrorBoundary extends Component<
  BriefingErrorBoundaryProps,
  BriefingErrorBoundaryState
> {
  state: BriefingErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): BriefingErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("BriefingErrorBoundary caught:", error, info.componentStack);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return <BriefingFallback error={this.state.error} onReset={this.handleReset} />;
    }
    return this.props.children;
  }
}
