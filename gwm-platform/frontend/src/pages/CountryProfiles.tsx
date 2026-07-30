import { useQuery } from '@tanstack/react-query'
import Navbar from '../components/Navbar'
import CountryCard from '../components/CountryCard'
import { fetchCountries } from '../services/countries'

export default function CountryProfiles() {
  const { data: countries = [], isLoading } = useQuery({
    queryKey: ['countries'],
    queryFn: fetchCountries,
  })

  return (
    <div className="animate-fade-in">
      <Navbar title="Country Profiles" subtitle="Supported geographic synthesis parameters" />

      <div className="p-8 space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading ? (
            <div className="col-span-full text-center text-slate-500 py-12">Loading profiles...</div>
          ) : (
            countries.map(country => (
              <CountryCard key={country.code} profile={country} />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
