import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext.new";
import { SecureAPI } from "../lib/secureApi";
import { RevenueSummary } from "./RevenueSummary";

function PropertyDashboard() {
  const [properties, setProperties] = useState<{ id: string; name: string }[]>();
  const [selectedProperty, setSelectedProperty] = useState("");
  const [propertyError, setPropertyError] = useState(false);

  useEffect(() => {
    let active = true;
    SecureAPI.getDashboardProperties().then(
      (items) => { if (active) setProperties(items); },
      () => { if (active) setPropertyError(true); },
    );
    return () => { active = false; };
  }, []);

  const propertyId = selectedProperty || properties?.[0]?.id;
  const [searchParams] = useSearchParams();
  const period = searchParams.get("month") ?? "";
  const [year, month] = period.split("-").map(Number);
  const validPeriod = /^\d{4}-(0[1-9]|1[0-2])$/.test(period) && year >= 1 && year <= 9998;

  return (
    <div className="p-4 lg:p-6 min-h-full">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 text-gray-900">Property Management Dashboard</h1>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 lg:p-6">
          <div className="mb-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
              <div>
                <h2 className="text-lg lg:text-xl font-medium text-gray-900 mb-2">Revenue Overview</h2>
                <p className="text-sm lg:text-base text-gray-600">
                  {validPeriod ? `Revenue for ${period}` : "All-time revenue for your properties"}
                </p>
              </div>

              {/* Property Selector */}
              <div className="flex flex-col sm:items-end">
                <label htmlFor="revenue-property" className="text-xs font-medium text-gray-700 mb-1">Select Property</label>
                <select
                  id="revenue-property"
                  value={propertyId ?? ""}
                  disabled={!propertyId}
                  onChange={(e) => setSelectedProperty(e.target.value)}
                  className="block w-full sm:w-auto min-w-[200px] px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  {!propertyId && <option value="">No property selected</option>}
                  {properties?.map((property) => (
                    <option key={property.id} value={property.id}>
                      {property.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {propertyError && <p role="alert">Failed to load properties.</p>}
            {period && !validPeriod && <p role="status">Use YYYY-MM for the month in the dashboard URL.</p>}
            {propertyId && (!period || validPeriod) && (
              <RevenueSummary
                key={JSON.stringify([propertyId, period])}
                propertyId={propertyId}
                year={validPeriod ? year : undefined}
                month={validPeriod ? month : undefined}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  return user ? <PropertyDashboard key={user.id} /> : null;
}
