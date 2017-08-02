#!/bin/bash

# vi:set tabstop=8 sts=8 shiftwidth=8 expandtab tw=80

set -eu

ask() {
	local q="$1"

	read -p "$q" -n 1 -r answer
	echo

	if [ "$answer" != "y" -a "$answer" != "Y" ]; then
		return 1
	fi

	return 0
}

echo "* determining main upstream branch"
if git branch -a -r| grep develop| grep -q "/develop"; then
	ref_branch="develop"
elif git branch -a -r| grep develop| grep -q "/master"; then
	ref_branch="master"
else
	echo "master or develop branches doesn't exist in remote"
	exit 1
fi
echo "reference upstream branch is $ref_branch"

echo
echo "* removing non-existent remote-tracking references"
git fetch --prune

echo
echo "* finding local branches that have been merged"
for branch in $(git branch --merged $ref_branch| grep -vE "develop|master"); do
	if ask "? delete merged branch $branch locally? (y/n)"; then
		git branch -D "$branch"
	fi
done

echo
echo "* finding remote branches that have been merged"
IFS=$'\n'
for ref in $(git branch  -r --merged $ref_branch | \
	     grep -vE "origin/develop|origin/master|origin/HEAD" | \
	     sed -e 's|origin/|origin |g' -e 's/^[[:space:]]*//g'); do
	repository=$(echo $ref | cut -d " " -f 1)
	branch=$(echo $ref | cut -d " " -f 2)
	if ask "? delete merged branch $repository/$branch remotely? (y/n)"; then
		git push -d "$repository" "$branch"
	fi
done

echo
echo "* finding branches that only exist locally"
echo "  might be work-in-progress branches! be careful! ACHTUNG!"
ask " do you understand? (y/n)" || exit 0
ask " really? (y/n)" || exit 0
ask " then let's continue (y/n)" || exit 0

IFS=$'\n'
for branch in $(git branch -vv| grep ': gone]'| awk '{ print $1 }'); do
	if ask "? delete local branch $repository/$branch? (y/n)"; then
		git branch -D "$branch"
	fi
done
