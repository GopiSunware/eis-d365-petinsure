"use client";

import Link from "next/link";
import { Plus, Calculator } from "lucide-react";

export default function QuotesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quotes</h1>
          <p className="text-gray-500 mt-1">
            Generate auto insurance premium quotes
          </p>
        </div>
        <Link href="/quotes/new" className="btn-primary flex items-center">
          <Plus className="h-4 w-4 mr-2" />
          New Quote
        </Link>
      </div>

      <div className="card text-center py-16">
        <Calculator className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900">
          Generate a New Quote
        </h2>
        <p className="text-gray-500 mt-2 max-w-md mx-auto">
          Our AI-powered rating engine calculates premiums based on driver
          profiles, vehicle information, and coverage selections.
        </p>
        <Link href="/quotes/new" className="btn-primary mt-6 inline-block">
          Start Quote
        </Link>
      </div>
    </div>
  );
}
