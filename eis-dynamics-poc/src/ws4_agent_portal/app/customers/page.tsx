"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { User, Mail, Phone, MapPin } from "lucide-react";
import { api, Customer } from "@/lib/api";
import { PageLoader } from "@/components/LoadingBar";

export default function CustomersPage() {
  const { data: customers, isLoading } = useQuery({
    queryKey: ["customers"],
    queryFn: () => api.getCustomers(),
  });

  if (isLoading) {
    return <PageLoader message="Loading customers..." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
        <p className="text-gray-500 mt-1">View and manage customer information</p>
      </div>

      {customers?.length === 0 ? (
        <div className="card text-center py-12">
          <User className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No customers found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {customers?.map((customer: Customer) => (
            <Link
              key={customer.customer_id}
              href={`/customers/${customer.customer_id}`}
              className="card hover:border-primary-200 hover:shadow-md transition-all"
            >
              <div className="flex items-start">
                <div className="h-12 w-12 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-primary-600 font-semibold text-lg">
                    {customer.first_name[0]}{customer.last_name[0]}
                  </span>
                </div>
                <div className="ml-4 flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 truncate">
                    {customer.first_name} {customer.last_name}
                  </h3>
                  <p className="text-sm text-gray-500">{customer.customer_id}</p>
                </div>
              </div>

              <div className="mt-4 space-y-2">
                {customer.email && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Mail className="h-4 w-4 mr-2 text-gray-400" />
                    <span className="truncate">{customer.email}</span>
                  </div>
                )}
                {customer.phone && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Phone className="h-4 w-4 mr-2 text-gray-400" />
                    {customer.phone}
                  </div>
                )}
                {customer.address && (
                  <div className="flex items-center text-sm text-gray-600">
                    <MapPin className="h-4 w-4 mr-2 text-gray-400 flex-shrink-0" />
                    <span className="truncate">{customer.address}</span>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
