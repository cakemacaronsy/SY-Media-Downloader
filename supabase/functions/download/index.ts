// Supabase Edge Function for media downloading
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { corsHeaders } from "../_shared/cors.ts"

interface DownloadRequest {
  url: string
  format: string
  resolution?: string
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { url, format, resolution } = await req.json() as DownloadRequest

    // Validate URL
    if (!url) {
      return new Response(
        JSON.stringify({ error: 'URL is required' }),
        { 
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // For Supabase, we'll use a different approach since yt-dlp isn't directly available
    // Option 1: Call an external API service that handles yt-dlp
    // Option 2: Use a cloud function with Python runtime
    // Option 3: Use a containerized solution
    
    // Example using an external service (you'd need to set this up)
    const externalApiUrl = Deno.env.get('DOWNLOAD_SERVICE_URL') || 'https://your-download-service.com'
    
    const response = await fetch(`${externalApiUrl}/download`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${Deno.env.get('SERVICE_API_KEY')}`
      },
      body: JSON.stringify({ url, format, resolution })
    })

    const data = await response.json()

    return new Response(
      JSON.stringify(data),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: response.status
      }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})
