import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts';

export default function AdverseEventsChart({ data }) {
    if (!data || data.length === 0) return null;

    // Modern vibrant colors for the bars
    const colors = ['#818CF8', '#A78BFA', '#F472B6', '#FB923C', '#FBBF24', '#34D399', '#2DD4BF', '#38BDF8'];

    return (
        <div className="w-full mt-4 bg-[#0A0C10] border border-white/5 rounded-2xl p-4 shadow-xl overflow-hidden">
            <h3 className="text-white text-md font-semibold mb-4 px-2 tracking-wide">Most Common Reported Reactions</h3>
            <div className="h-[250px] w-full text-xs">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={data}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                        barSize={16}
                    >
                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#334155" opacity={0.3} />
                        <XAxis type="number" hide />
                        <YAxis
                            dataKey="term"
                            type="category"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#94A3B8', fontSize: 11 }}
                            width={120}
                        />
                        <Tooltip
                            cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                            contentStyle={{
                                backgroundColor: '#1E293B',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: '8px',
                                color: '#FFF',
                                fontSize: '12px'
                            }}
                            itemStyle={{ color: '#E2E8F0' }}
                        />
                        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                            {
                                data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                ))
                            }
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
