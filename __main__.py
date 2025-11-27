import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';

// --- Utility Functions for API Call and Exponential Backoff ---

/**
 * Executes a fetch request with exponential backoff for resilience.
 * @param {string} url The API endpoint URL.
 * @param {object} options The fetch options.
 * @param {number} retries The number of retries remaining.
 * @returns {Promise<Response>} The fetch response.
 */
const fetchWithBackoff = async (url, options, retries = 3) => {
    try {
        const response = await fetch(url, options);
        if (response.status === 429 && retries > 0) {
            const delay = Math.pow(2, 3 - retries) * 1000;
            console.warn(`Rate limit exceeded (429). Retrying in ${delay / 1000}s... (Retries left: ${retries - 1})`);
            await new Promise(resolve => setTimeout(resolve, delay));
            return fetchWithBackoff(url, options, retries - 1);
        }
        return response;
    } catch (error) {
        if (retries > 0) {
            const delay = Math.pow(2, 3 - retries) * 1000;
            console.warn(`Fetch failed (Network error). Retrying in ${delay / 1000}s... (Retries left: ${retries - 1})`);
            await new Promise(resolve => setTimeout(resolve, delay));
            return fetchWithBackoff(url, options, retries - 1);
        }
        throw error;
    }
};

// --- Main Application Component ---

const App = () => {
    const [searchTerm, setSearchTerm] = useState("camera");
    const [deal, setDeal] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Using the user-provided API Key explicitly.
    const apiKey = ""; 
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;

    const handleSearch = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setDeal(null);

        // UPDATED SYSTEM PROMPT: Forces JSON output without using the responseSchema (which conflicts with the search tool).
        const systemPrompt = "You are a deal extraction agent. The user is querying for a current deal on a specific item from Slickdeals. Search the web and find the single, most recent and relevant deal for the term provided. Extract ONLY the deal's title, the final price, the direct link to the retailer (or the Slickdeals thread if retailer link is not immediately clear), and any associated image URL if available. Provide the response as a valid, pure JSON object with the keys: 'title', 'price', 'link', and 'imageUrl'. DO NOT include any introductory text, markdown formatting (like ```json), or explanations outside of the JSON object itself. The keys are mandatory.";
        
        const userQuery = `Find the best and most current Slickdeals thread for: ${searchTerm}. Use this information to fill the JSON fields.`;

        const payload = {
            contents: [{ parts: [{ text: userQuery }] }],
            // Keep the Google Search grounding tool
            tools: [{ "google_search": {} }],
            systemInstruction: { parts: [{ text: systemPrompt }] },
            // REMOVED: generationConfig with responseMimeType/responseSchema to fix 400 error.
        };

        try {
            const response = await fetchWithBackoff(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            // Check for non-OK response status before parsing
            if (!response.ok) {
                const errorBody = await response.text();
                // Throw an error with the status code and a snippet of the body
                throw new Error(`API returned error status ${response.status}: ${errorBody.substring(0, 100)}...`);
            }

            const result = await response.json();
            
            const jsonText = result.candidates?.[0]?.content?.parts?.[0]?.text;
            
            if (jsonText) {
                // The model returns the pure JSON string based on the System Instruction
                const parsedDeal = JSON.parse(jsonText);
                setDeal(parsedDeal);
            } else {
                setError("Could not parse the deal information from the model response. Response was empty.");
            }

        } catch (err) {
            console.error("API Fetch Error:", err);
            // Display the specific error message if available, otherwise a generic one
            if (err.message) {
                 setError(`API Error: ${err.message}`); 
            } else {
                 // Generic network or fetch failure
                 setError("Failed to connect to the Gemini API. Check your network or try again.");
            }
        } finally {
            setLoading(false);
        }
    };

    // Auto-run search on initial load for the default term "camera"
    useEffect(() => {
        handleSearch({ preventDefault: () => {} }); // Pass mock event object
    }, []);

    return (
        <div className="min-h-screen bg-gray-50 p-4 sm:p-8">
            <header className="text-center mb-8">
                <h1 className="text-4xl font-extrabold text-indigo-700">Live Deal Finder</h1>
                <p className="text-gray-500 mt-2">Powered by the Gemini API & Google Search Grounding</p>
            </header>

            <div className="max-w-xl mx-auto bg-white shadow-xl rounded-2xl p-6">
                
                {/* Search Form */}
                <form onSubmit={handleSearch} className="flex gap-2 mb-6">
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="e.g., camera, laptop, headphones"
                        className="flex-grow p-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 transition duration-150"
                        required
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className={`px-6 py-3 rounded-lg font-semibold text-white transition duration-150 flex items-center justify-center
                            ${loading ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-500 focus:ring-opacity-50'}
                        `}
                    >
                        {loading ? (
                            <svg className="animate-spin h-5 w-5 text-white" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        ) : (
                            <><Search className="w-5 h-5 mr-2" /> Find Deal</>
                        )}
                    </button>
                </form>

                {/* Status and Results Area */}
                <div className="min-h-48 flex items-center justify-center">
                    {error && (
                        <div className="text-red-600 p-4 border border-red-300 bg-red-50 rounded-lg w-full text-center">
                            {error}
                        </div>
                    )}
                    
                    {!loading && !deal && !error && (
                        <p className="text-gray-400">Search for a product to see the best current deal.</p>
                    )}

                    {deal && (
                        <div className="w-full space-y-4">
                            <h2 className="text-2xl font-bold text-gray-800 border-b pb-2">Top Deal Found</h2>
                            
                            <div className="flex flex-col sm:flex-row gap-4 bg-gray-50 p-4 rounded-xl shadow-inner">
                                {/* Image Column */}
                                <div className="flex-shrink-0 w-full sm:w-32 h-32 overflow-hidden rounded-lg">
                                    <img
                                        src={deal.imageUrl || "[https://placehold.co/128x128/f0f0f0/888888?text=NO+IMAGE](https://placehold.co/128x128/f0f0f0/888888?text=NO+IMAGE)"}
                                        alt={deal.title}
                                        className="w-full h-full object-cover"
                                        onError={(e) => {
                                            e.target.onerror = null; // Prevents infinite loop
                                            e.target.src = "[https://placehold.co/128x128/f0f0f0/888888?text=Image+Error](https://placehold.co/128x128/f0f0f0/888888?text=Image+Error)";
                                        }}
                                    />
                                </div>
                                
                                {/* Details Column */}
                                <div className="flex-grow">
                                    <p className="text-xl font-extrabold text-green-600 mb-1">{deal.price}</p>
                                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{deal.title}</h3>
                                    
                                    <a 
                                        href={deal.link} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center px-4 py-2 bg-indigo-500 text-white text-sm font-medium rounded-full hover:bg-indigo-600 transition duration-150"
                                    >
                                        Go to Deal
                                    </a>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default App;