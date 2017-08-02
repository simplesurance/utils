#!/bin/bash

# vi:set tabstop=8 sts=8 shiftwidth=8 expandtab tw=80

set -u

ask() {
	local q="$1"

	read -p "$q" -n 1 answer
	echo

	if [ "$answer" != "y" -a "$answer" != "Y" ]; then
		return 1
	fi

	return 0
}

rm_local_merged_branches() {
	echo
	echo "* finding local branches that have been merged"
	local branches="$(git branch --merged $ref_branch|\
			  grep -vE "develop|master")"

	if [ -z "$branches" ]; then
		echo "no branches found"
		return
	fi

	echo "$branches"
	echo
	if ask "? delete those merged branches locally? (y/n)"; then
		for branch in $branches; do
			git branch -D "$branch"
		done
	fi
}

rm_only_local_branches() {
	echo
	echo "* finding branches that only exist locally"
	branches="$(git branch -vv| grep ': gone]'| \
		    sed -e 's/^[[:space:]]*//g')"

	if [ -z "$branches" ]; then
		echo "no branches found"
		return
	fi

	echo "  might be work-in-progress branches! be careful! ACHTUNG!"
	ask " do you understand? (y/n)" || exit 0
	ask " really? (y/n)" || exit 0
	ask " then let's continue (y/n)" || exit 0

	IFS=$'\n'
	for branch in $branches; do
		if ask "? delete local branch $branch? (y/n)"; then
			git branch -D "$branch"
		fi
	done
}

rm_local_branches() {
	echo
	echo "* finding local branches"

	IFS=$'\n'
	for branch in $(git branch | grep -vE "develop|master" | \
			sed -e 's/^**[[:space:]]*//g'); do
		if ask "? delete local branch $branch? (y/n)"; then
			git branch -D "$branch"
		fi
	done

}

rm_remote_merged_branches() {
	echo
	echo "* finding remote branches that have been merged"
	IFS=$'\n'
	local branches="$(git branch  -r --merged $ref_branch | \
			  grep -vE "origin/develop|origin/master|origin/HEAD" | \
			  sed -e 's|origin/|origin |g' -e 's/^[[:space:]]*//g')"

	if [ -z "$branches" ]; then
		echo "no branches found"
		return
	fi
	echo "$branches"
	echo

	if ask "? delete those merged branches remotely? (y/n)"; then
		for ref in $branches; do
			local repository=$(echo $ref | cut -d " " -f 1)
			local branch=$(echo $ref | cut -d " " -f 2)
			git push -d "$repository" "$branch"
		done
	fi
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

echo "-------------------------------------"
rm_local_merged_branches
echo "-------------------------------------"
rm_remote_merged_branches
echo "-------------------------------------"
rm_only_local_branches
echo "-------------------------------------"
rm_local_branches
