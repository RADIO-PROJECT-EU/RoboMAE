% RoboMAE, The Roboskel Multimodal Annotation Environment,
% is developed as part of Roboskel, the robotics activity
% of the Institute of Informatics and Telecommunications,
% National Centre for Scientific Research "Demokritos",
% Ag. Paraskevi, Greece
% Please see http://roboskel.iit.demokritos.gr
% or contact us at roboskel@iit.demokritos.gr
% 
% Copyright (C) 2012-2013, NCSR "Demokritos", Ag. Paraskevi, Greece
% Copyright (C) 2013, Konstantinos Tsiakas
% 
% Authors:
% Sergios Petridis, 2012
% Theodore Giannakopoulos, 2012-2013
% Konstantinos Tsiakas, 2013
% 
% This file is part of RoboMAE.
% 
% RoboMAE is free software: you can redistribute it and/or modify
% it under the terms of the GNU General Public License as published by
% the Free Software Foundation, either version 2 of the License, or
% (at your option) any later version.
% 
% RoboMAE is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
% GNU General Public License for more details.
% 
% You should have received a copy of the GNU General Public License
% along with RoboMAE.  If not, see <http://www.gnu.org/licenses/>.

function [purityClusterMean, puritySpeakerMean, purityCluster, puritySpeaker] = computeErrorClusterPurityMatrix(n)
[Nc, Ns] = size(n);

N_s = sum(n,1);
N_c = sum(n,2)';
N   = sum(sum(n));

% compute cluster purity:
for (i=1:Nc)
    purityCluster(i) = max( (n(i,:)) )/ (N_c(i)+eps);
	%purityCluster(i) = sum( (n(i,:)).^2./ (N_c(i)).^2 );
end

% compute speaker purity:
for (j=1:Ns)
    puritySpeaker(j) = max( (n(:,j)) )/ (N_s(j)+eps);
	%puritySpeaker(j) = sum( (n(:,j)).^2./ (N_s(j)).^2 );
end

purityClusterMean = sum(purityCluster.*N_c) / N;
puritySpeakerMean = sum(puritySpeaker.*N_s) / N;

%fprintf('%10.3f%10.3f%10.3f\n', purityClusterMean, puritySpeakerMean, mean([purityClusterMean puritySpeakerMean]));
