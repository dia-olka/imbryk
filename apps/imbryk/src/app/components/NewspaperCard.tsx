import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { RoutingDetail } from '../api/types';

interface NewspaperCardProps {
  routing: RoutingDetail;
  paperName: string;
  tagline: string;
}

export function NewspaperCard({ routing, paperName, tagline }: NewspaperCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{paperName}</CardTitle>
        <CardDescription className="italic">{tagline}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-1.5">
          {routing.matched_categories.map((cat) => (
            <Badge key={cat} variant="secondary" className="text-xs">
              {cat}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
